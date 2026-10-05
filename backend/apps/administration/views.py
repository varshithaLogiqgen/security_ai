import hashlib
import secrets
from datetime import timedelta
from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError,NotFound
from apps.core.api import endpoint,require,object_or_404,validated,page
from apps.identity.models import User
from apps.people.serializers import person
from apps.projects.models import Team,Project
from apps.audit.service import record
from .models import Approval,Invitation
from .serializers import InviteInput,TeamInput,ProjectInput,AccessRequestInput,ReviewInput,ReasonInput
from .services import approval_data,can_view,review

@endpoint(['GET'])
def users(request):
    require(request.user,'admin')
    term=request.query_params.get('q','')[:300]
    rows=User.objects.filter(organization=request.user.organization).filter(Q(name__icontains=term)|Q(email__icontains=term)).order_by('name','id')
    return Response(page(request,rows,person))

@endpoint(['POST'])
def invitations(request):
    require(request.user,'admin')
    data=validated(InviteInput,request)
    token=secrets.token_urlsafe(32)
    obj=Invitation.objects.create(organization=request.user.organization,email=data['email'].lower(),invited_by=request.user,token_hash=hashlib.sha256(token.encode()).hexdigest(),expires_at=timezone.now()+timedelta(days=7))
    record(request.user,'admin.invitation.created',obj.pk)
    return Response({'id':str(obj.pk),'status':'pending','invitation_url':request.build_absolute_uri(f'/api/v1/auth/accept?token={token}')},status=201)

@endpoint(['GET','POST'])
def teams(request):
    require(request.user,'admin')
    if request.method=='POST':
        data=validated(TeamInput,request)
        obj=Team.objects.create(organization=request.user.organization,name=data['name'])
        record(request.user,'admin.team.created',obj.pk)
        return Response({'id':str(obj.pk),'name':obj.name},status=201)
    rows=Team.objects.filter(organization=request.user.organization,name__icontains=request.query_params.get('q','')[:300]).order_by('name','id')
    return Response(page(request,rows,lambda t:{'id':str(t.pk),'name':t.name}))

@endpoint(['GET','POST'])
def projects(request):
    require(request.user,'admin')
    if request.method=='POST':
        data=validated(ProjectInput,request)
        steward=object_or_404(User,data['steward_user_id'],request.user)
        if steward.pk==request.user.pk or not steward.is_active: raise ValidationError('Choose an independent active project steward.')
        obj=Project.objects.create(organization=request.user.organization,name=data['name'],description=data.get('description',''),code=data['name'][:2].upper(),steward=steward)
        record(request.user,'admin.project.created',obj.pk)
        return Response({'id':str(obj.pk),'name':obj.name},status=201)
    rows=Project.objects.filter(organization=request.user.organization,name__icontains=request.query_params.get('q','')[:300]).order_by('name','id')
    return Response(page(request,rows,lambda p:{'id':str(p.pk),'name':p.name}))

@endpoint(['POST'])
def access_requests(request):
    require(request.user,'admin')
    data=validated(AccessRequestInput,request)
    target=object_or_404(User,data['target_user_id'],request.user)
    scope=object_or_404(Project if data['action']=='project_membership' else Team,data['scope_id'],request.user)
    if not target.is_active or not scope.is_active or data['expires_at']<=timezone.now(): raise ValidationError('Choose an active colleague, active scope and a future expiry.')
    approval=Approval.objects.create(organization=request.user.organization,requester=request.user,kind=data['action'],target_user=target,scope_id=scope.pk,reason=data['reason'],payload={'operation':data['operation'],'valid_to':data['expires_at'].isoformat()},expires_at=min(data['expires_at'],timezone.now()+timedelta(days=7)))
    record(request.user,'admin.access.proposed',approval.pk)
    return Response(approval_data(approval,request.user),status=202)

@endpoint(['POST'])
def deactivate(request,pk):
    require(request.user,'admin')
    target=object_or_404(User,pk,request.user)
    data=validated(ReasonInput,request)
    approval=Approval.objects.create(organization=request.user.organization,requester=request.user,kind='deactivate',target_user=target,scope_id=target.pk,reason=data['reason'],payload={'target':str(target.pk)},expires_at=timezone.now()+timedelta(days=7))
    record(request.user,'admin.deactivation.proposed',approval.pk)
    return Response(approval_data(approval,request.user),status=202)

@endpoint(['GET'])
def approvals(request):
    # Stewards and retention/security reviewers have scoped access without content-admin rights.
    rows=Approval.objects.filter(organization=request.user.organization).order_by('-created_at','id')
    rows=[a for a in rows if can_view(a,request.user)]
    term=request.query_params.get('q','').lower()[:300]
    if term: rows=[a for a in rows if term in f'{a.kind} {a.reason} {a.status}'.lower()]
    return Response(page(request,rows,lambda a:approval_data(a,request.user)))

@endpoint(['POST'])
def approval_review(request,pk):
    approval=object_or_404(Approval,pk,request.user)
    if not can_view(approval,request.user): raise NotFound()
    data=validated(ReviewInput,request)
    result=review(approval,request.user,**data)
    return Response(approval_data(result,request.user))
