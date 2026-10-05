from datetime import timedelta
from django.utils import timezone
from rest_framework.exceptions import NotFound,ValidationError
from apps.policy.service import role,member,team_member,active
from apps.core.api import object_or_404,Conflict
from apps.audit.service import record
from apps.projects.models import Project,Team,ProjectMembership,TeamMembership,TeamLead
from apps.documents.models import Document
from apps.work_updates.models import WorkUpdate
from apps.notifications.models import Notification
from .models import Approval,ApprovalReview

def reviewer_role(approval,user):
    if approval.status!='pending' or approval.expires_at<=timezone.now() or user.pk in {approval.requester_id,approval.target_user_id}: return None
    if approval.reviews.filter(reviewer=user).exists(): return None
    if approval.kind=='document_widen':
        doc=Document.objects.filter(pk=approval.scope_id,organization=user.organization).first()
        return 'steward' if doc and doc.project.steward_id==user.pk and doc.uploader_id!=user.pk else None
    if approval.kind in {'document_delete','update_delete'}: return 'retention' if role(user,'retention') else None
    if role(user,'admin') and not approval.reviews.filter(role='admin',decision='approve').exists(): return 'admin'
    if approval.requester_id==approval.target_user_id and role(user,'audit') and not approval.reviews.filter(role='audit',decision='approve').exists(): return 'audit'
    return None

def can_view(approval,user):
    if approval.organization_id!=user.organization_id: return False
    if approval.requester_id==user.pk or approval.target_user_id==user.pk or approval.reviews.filter(reviewer=user).exists(): return True
    if approval.kind in {'project_membership','team_membership','team_lead','deactivate'}: return role(user,'admin') or (role(user,'audit') and approval.target_user_id==approval.requester_id)
    if approval.kind=='document_widen': return Document.objects.filter(pk=approval.scope_id,organization=user.organization,project__steward=user).exists()
    return role(user,'retention')

def approval_data(approval,user):
    return {'id':str(approval.pk),'requester':approval.requester.name,'scope':f'{approval.kind} · {approval.scope_id}','reason':approval.reason,'status':'expired' if approval.status=='pending' and approval.expires_at<=timezone.now() else approval.status,'can_review':bool(reviewer_role(approval,user))}

def widening_request(user,doc):
    if doc.uploader_id==doc.project.steward_id: raise ValidationError('An independent project steward must be assigned first.')
    obj,_=Approval.objects.get_or_create(organization=user.organization,requester=user,kind='document_widen',scope_id=doc.pk,status='pending',defaults={'reason':'Widen document access to project members','payload':{'version':doc.version},'expires_at':timezone.now()+timedelta(days=7)})
    record(user,'approval.widen_requested',obj.pk)
    return obj

def removal_request(user,obj,kind):
    approval,_=Approval.objects.get_or_create(organization=user.organization,requester=user,kind=kind,scope_id=obj.pk,status='pending',defaults={'reason':'Owner requested removal through the retention workflow','payload':{'version':obj.version},'expires_at':timezone.now()+timedelta(days=7)})
    record(user,'approval.removal_requested',approval.pk)
    return approval

def apply(approval,reviewer):
    if approval.kind in {'document_widen','document_delete','update_delete'}:
        model=WorkUpdate if approval.kind=='update_delete' else Document
        obj=object_or_404(model,approval.scope_id,reviewer)
        if obj.version!=approval.payload['version'] or obj.status=='deleted': raise Conflict()
        if approval.kind=='document_widen':
            if not member(obj.uploader,obj.project) or not obj.ever_published: raise ValidationError('The request is no longer eligible.')
            obj.classification='project'
        else:
            if obj.legal_hold: raise ValidationError('This record is on legal hold.')
            obj.status='deleted'
        obj.version+=1;obj.save()
    elif approval.kind=='deactivate':
        user=approval.target_user
        user.is_active=False;user.session_version+=1;user.save(update_fields=['is_active','session_version'])
    else:
        target=approval.target_user
        from django.utils.dateparse import parse_datetime
        if not target or not target.is_active or parse_datetime(approval.payload['valid_to'])<=timezone.now(): raise ValidationError('The request is no longer eligible.')
        project_assignment=approval.kind=='project_membership'
        scope=object_or_404(Project if project_assignment else Team,approval.scope_id,reviewer)
        if not scope.is_active: raise ValidationError('The workspace is no longer active.')
        model={'project_membership':ProjectMembership,'team_membership':TeamMembership,'team_lead':TeamLead}[approval.kind]
        fields={'organization':reviewer.organization,'user':target,'project' if project_assignment else 'team':scope}
        model.objects.filter(**fields,revoked_at__isnull=True).update(revoked_at=timezone.now())
        if approval.payload['operation']=='assign':
            from django.utils.dateparse import parse_datetime
            model.objects.create(**fields,valid_to=parse_datetime(approval.payload['valid_to']),assigned_by=reviewer)
    record(reviewer,f'admin.{approval.kind}.applied',approval.scope_id)

def review(approval,user,decision,reason):
    review_role=reviewer_role(approval,user)
    if not review_role: raise NotFound()
    ApprovalReview.objects.create(organization=user.organization,approval=approval,reviewer=user,role=review_role,decision=decision,reason=reason)
    if decision=='reject': approval.status='rejected'
    else:
        roles=set(approval.reviews.filter(decision='approve').values_list('role',flat=True))
        needs_two=approval.target_user_id==approval.requester_id
        if not needs_two or {'admin','audit'}.issubset(roles):
            apply(approval,user)
            approval.status='approved'
    approval.save()
    record(user,'approval.reviewed',approval.pk,reason=decision)
    Notification.objects.create(organization=user.organization,user=approval.requester,message='An access or removal request has been reviewed.')
    return approval
