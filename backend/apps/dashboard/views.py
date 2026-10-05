"""Role summaries use live permissions for every count and record."""
from datetime import datetime, time, timedelta
from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from apps.core.api import endpoint
from apps.policy.service import visible_documents, visible_updates, active, role
from apps.projects.models import ProjectMembership, Project, Team, TeamLead
from apps.projects.serializers import project_data
from apps.work_updates.serializers import update_data
from apps.documents.serializers import document_data
from apps.documents.models import ProcessingJob
from apps.identity.models import User
from apps.administration.models import Invitation, Approval
from apps.administration.services import approval_data, can_view
from apps.audit.models import AuditEvent


class Filters(serializers.Serializer):
    view=serializers.ChoiceField(choices=['employee','lead','admin','security'],required=False)
    date=serializers.DateField(required=False)
    event=serializers.ChoiceField(choices=['all','denials','permissions','scans','sessions'],default='all')


def event_data(event):
    return {'id':str(event.pk),'actor':str(event.actor_id or ''),'action':event.action,'target':event.target,'decision':event.decision,'reason':event.reason,'policy_version':event.policy_version,'date':event.created_at.isoformat()}


@endpoint(['GET'])
def overview(request):
    user=request.user
    filters=Filters(data=request.query_params)
    filters.is_valid(raise_exception=True)
    data=filters.validated_data
    led=Team.objects.filter(organization=user.organization,is_active=True,pk__in=active(TeamLead.objects.filter(organization=user.organization,user=user)).values('team_id')).order_by('name','id')
    available=['employee']
    if led.exists(): available.append('lead')
    if role(user,'admin'): available.append('admin')
    if role(user,'audit'): available.append('security')
    view=data.get('view',available[-1])
    if view not in available: raise NotFound()
    selected=data.get('date',timezone.localdate())
    result={'view':view,'available_views':available,'date':selected.isoformat(),'event':data['event']}
    projects=Project.objects.filter(organization=user.organization,is_active=True,pk__in=active(ProjectMembership.objects.filter(organization=user.organization,user=user)).values('project_id')).order_by('name','id')
    own=visible_updates(user).filter(owner=user).select_related('owner','team').order_by('-work_date','-created_at','id')
    if view=='employee':
        docs=visible_documents(user).select_related('project','uploader','current_version').order_by('-updated_at','id')
        result.update(cards={'drafts':own.filter(status='draft').count(),'published':own.filter(status='published').count(),'projects':projects.count(),'documents':docs.count()},updates=[update_data(u,user) for u in own[:5]],projects=[project_data(p) for p in projects[:5]],documents=[document_data(d,user) for d in docs[:5]])
    elif view=='lead':
        shared=visible_updates(user).filter(team__in=led,status='published',visibility='lead_visible').select_related('owner','team')
        day=shared.filter(work_date=selected).order_by('-created_at','id')
        result.update(cards={'teams':led.count(),'updates_today':shared.filter(work_date=timezone.localdate()).count(),'blockers':day.filter(is_blocked=True).count(),'projects':projects.count()},teams=[{'id':str(t.pk),'name':t.name,'updates':[update_data(u,user) for u in day.filter(team=t)[:10]],'count':day.filter(team=t).count()} for t in led],blockers=[update_data(u,user) for u in day.filter(is_blocked=True)[:10]],updates=[update_data(u,user) for u in own[:5]])
    elif view=='admin':
        accounts=User.objects.filter(organization=user.organization).order_by('name','id')
        invitations=Invitation.objects.filter(organization=user.organization,accepted_at__isnull=True,expires_at__gt=timezone.now()).order_by('-created_at')
        approvals=Approval.objects.filter(organization=user.organization,status='pending',expires_at__gt=timezone.now()).order_by('-created_at')
        changes=AuditEvent.objects.filter(organization=user.organization,actor=user,action__startswith='admin.').order_by('-created_at')
        result.update(cards={'accounts':accounts.filter(is_active=True).count(),'invitations':invitations.count(),'teams':Team.objects.filter(organization=user.organization,is_active=True).count(),'projects':Project.objects.filter(organization=user.organization,is_active=True).count()},accounts=[{'id':str(u.pk),'name':u.name,'email':u.email,'active':u.is_active} for u in accounts[:10]],invitations=[{'id':str(i.pk),'email':i.email,'expires_at':i.expires_at.isoformat()} for i in invitations[:10]],approvals=[approval_data(a,user) for a in approvals if can_view(a,user)][:10],events=[event_data(e) for e in changes[:10]])
    else:
        start=timezone.make_aware(datetime.combine(selected,time.min))
        end=timezone.make_aware(datetime.combine(selected+timedelta(days=1),time.min))
        events=AuditEvent.objects.filter(organization=user.organization,created_at__gte=start,created_at__lt=end)
        permissions=Q(action='document.access_changed')|Q(action__startswith='admin.',action__endswith='.applied')
        security=Q(decision='deny')|Q(action__startswith='session.')|Q(action__startswith='approval.')|permissions|Q(action='document.processed')
        rows=events.filter(security)
        choices={'denials':Q(decision='deny'),'permissions':permissions,'scans':Q(action='document.processed'),'sessions':Q(action__startswith='session.')}
        if data['event'] in choices: rows=rows.filter(choices[data['event']])
        result.update(cards={'denials':events.filter(decision='deny').count(),'events':events.filter(security).count(),'permissions':events.filter(permissions).count(),'failed_scans':ProcessingJob.objects.filter(organization=user.organization,status='failed',completed_at__gte=start,completed_at__lt=end,error_code__in=['malware_detected','scanner_unavailable']).count()},events=[event_data(e) for e in rows.order_by('-created_at','id')[:30]],changes=[event_data(e) for e in events.filter(permissions).order_by('-created_at','id')[:10]],security_settings=[{'name':'Authentication','value':'Organization SSO' if settings.OIDC_ISSUER else 'Synthetic local sign-in'},{'name':'Malware scanner','value':settings.SCANNER_MODE},{'name':'AI provider approval','value':settings.AI_APPROVAL_REFERENCE or 'Not approved'},{'name':'Retention policy','value':settings.RETENTION_POLICY_REFERENCE or 'Not configured'},{'name':'Authorization','value':'Live memberships and grants; default deny'}])
    return Response(result)
