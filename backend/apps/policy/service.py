"""Single live policy boundary. Administrative titles never bypass content policy."""
from dataclasses import dataclass
from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from apps.identity.models import User, UserRole
from apps.projects.models import ProjectMembership, TeamMembership, TeamLead

POLICY_VERSION = '2026-10-v1'

def active(qs):
    now = timezone.now()
    return qs.filter(valid_from__lte=now, revoked_at__isnull=True).filter(Q(valid_to__isnull=True) | Q(valid_to__gt=now))

def live(user):
    if not user or not user.is_authenticated or not settings.POLICY_ENABLED:
        return None
    return User.objects.filter(pk=user.pk, is_active=True, organization__is_active=True).first()

def role(user, name):
    current = live(user)
    return bool(current and active(UserRole.objects.filter(user=current, organization=current.organization, role=name)).exists())

def member(user, project):
    return bool(project.is_active and project.organization_id == user.organization_id and active(ProjectMembership.objects.filter(organization=user.organization, user=user, project=project)).exists())

def team_member(user, team):
    return bool(team.is_active and team.organization_id == user.organization_id and active(TeamMembership.objects.filter(organization=user.organization,user=user,team=team)).exists())

def leads(user, team):
    return bool(team.is_active and team.organization_id == user.organization_id and active(TeamLead.objects.filter(organization=user.organization,user=user,team=team)).exists())

@dataclass(frozen=True)
class Decision:
    allow: bool
    permitted_fields: tuple = ()
    reason_code: str = 'policy_denied'
    policy_version: str = POLICY_VERSION

def authorize(subject, action, resource=None):
    user = live(subject)
    if not user:
        return Decision(False, reason_code='inactive_or_policy_unavailable')
    if resource is not None and getattr(resource, 'organization_id', None) != user.organization_id:
        return Decision(False, reason_code='scope_denied')
    allowed = False
    fields = ()
    if action == 'admin': allowed = role(user, 'admin')
    elif action == 'audit': allowed = role(user, 'audit')
    elif action == 'profile.read':
        allowed = resource.is_active
        fields = ('id','name','email','title','team','bio')
    elif action in {'profile.edit','personal.read','personal.edit'}: allowed = resource.id == user.id
    elif action == 'project.read': allowed = member(user,resource)
    elif action == 'update.create': allowed = team_member(user,resource)
    elif action == 'team.updates': allowed = leads(user,resource)
    elif action == 'update.read':
        allowed = resource.status != 'deleted' and (resource.owner_id == user.id or (resource.status in {'published','deletion_requested'} and resource.visibility == 'lead_visible' and leads(user,resource.team)))
    elif action == 'update.edit': allowed = resource.owner_id == user.id and resource.status != 'deleted'
    elif action == 'document.upload': allowed = member(user,resource)
    elif action == 'document.manage': allowed = resource.uploader_id == user.id and resource.status != 'deleted' and member(user,resource.project)
    elif action in {'document.read','document.download','document.retrieve'}:
        if member(user,resource.project) and resource.status != 'deleted':
            if resource.status in {'published','deletion_requested'}:
                allowed = resource.classification == 'project' or active(resource.grants.filter(organization=user.organization,grantee=user)).exists()
            elif action == 'document.read':
                allowed = resource.uploader_id == user.id
    elif action == 'conversation.read': allowed = resource.owner_id == user.id and not resource.is_deleted
    return Decision(bool(allowed), fields, 'allowed' if allowed else 'policy_denied')

def visible_updates(user):
    from apps.work_updates.models import WorkUpdate
    if not live(user): return WorkUpdate.objects.none()
    teams = active(TeamLead.objects.filter(user=user,organization=user.organization,team__is_active=True)).values('team_id')
    return WorkUpdate.objects.filter(organization=user.organization).exclude(status='deleted').filter(Q(owner=user) | Q(team_id__in=teams,status__in=['published','deletion_requested'],visibility='lead_visible'))

def visible_documents(user, published_only=False):
    from apps.documents.models import Document, DocumentGrant
    if not live(user): return Document.objects.none()
    projects = active(ProjectMembership.objects.filter(user=user,organization=user.organization,project__is_active=True)).values('project_id')
    granted = active(DocumentGrant.objects.filter(grantee=user,organization=user.organization)).values('document_id')
    published = Q(status__in=['published','deletion_requested']) & (Q(classification='project') | Q(pk__in=granted))
    visible = published if published_only else published | Q(uploader=user,status__in=['processing','unpublished','quarantined','failed'])
    return Document.objects.filter(organization=user.organization,project_id__in=projects).filter(visible)
