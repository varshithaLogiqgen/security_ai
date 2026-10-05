from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, NotFound
from apps.core.api import endpoint, require, object_or_404, validated, version_check, page
from apps.policy.service import visible_updates, authorize
from apps.audit.service import record
from apps.projects.models import Team
from .models import WorkUpdate, UpdateRevision
from .serializers import CreateUpdate, EditUpdate, PublishUpdate, update_data

@endpoint(['GET','POST'])
def updates(request):
    if request.method == 'POST':
        data = validated(CreateUpdate,request)
        team = object_or_404(Team,data.pop('team_id'),request.user)
        require(request.user,'update.create',team)
        obj = WorkUpdate.objects.create(organization=request.user.organization,owner=request.user,team=team,**data)
        record(request.user,'update.created',obj.pk)
        return Response(update_data(obj,request.user),status=201)
    return list_updates(request,visible_updates(request.user).filter(owner=request.user))

def list_updates(request,rows):
    status = request.query_params.get('status')
    if status: rows = rows.filter(status=status)
    rows = rows.order_by('-work_date','-created_at','id')
    return Response(page(request,[r for r in rows if authorize(request.user,'update.read',r).allow],lambda r:update_data(r,request.user)))

@endpoint(['GET'])
def team_updates(request,pk):
    team = object_or_404(Team,pk,request.user)
    require(request.user,'team.updates',team)
    return list_updates(request,visible_updates(request.user).filter(team=team,status='published',visibility='lead_visible'))

def revise(obj,user):
    if obj.status in {'published','deletion_requested'}:
        UpdateRevision.objects.create(organization=obj.organization,update=obj,version=obj.version,body=obj.body,visibility=obj.visibility,edited_by=user)
    obj.version += 1

@endpoint(['GET','PATCH','DELETE'])
def update(request,pk):
    obj = object_or_404(WorkUpdate,pk,request.user)
    require(request.user,'update.read' if request.method=='GET' else 'update.edit',obj)
    if request.method != 'GET': version_check(request,obj)
    if request.method == 'DELETE':
        if obj.status != 'draft': raise ValidationError('Published updates require a removal request.')
        record(request.user,'update.draft_deleted',obj.pk)
        obj.delete()
        return Response(status=204)
    if request.method == 'PATCH':
        data = validated(EditUpdate,request)
        if 'team_id' in data and data['team_id'] != obj.team_id: raise ValidationError('The team cannot be changed.')
        if obj.status == 'draft' and data.get('visibility','private') != 'private': raise ValidationError('Drafts must remain private.')
        revise(obj,request.user)
        for key in ['body','visibility','work_date','is_blocked']:
            if key in data: setattr(obj,key,data[key])
        obj.save()
        record(request.user,'update.revised',obj.pk)
    return Response(update_data(obj,request.user))

@endpoint(['POST'])
def publish(request,pk):
    obj = object_or_404(WorkUpdate,pk,request.user)
    require(request.user,'update.edit',obj)
    version_check(request,obj)
    if obj.status != 'draft': raise ValidationError('Only a draft can be published.')
    data = validated(PublishUpdate,request)
    obj.visibility = data['visibility']
    obj.status = 'published'
    obj.version += 1
    obj.save()
    record(request.user,'update.published',obj.pk)
    return Response(update_data(obj,request.user))

@endpoint(['POST'])
def request_deletion(request,pk):
    from apps.administration.services import removal_request
    obj = object_or_404(WorkUpdate,pk,request.user)
    require(request.user,'update.edit',obj)
    version_check(request,obj)
    if obj.status != 'published': raise ValidationError('Only published updates need removal approval.')
    removal_request(request.user,obj,'update_delete')
    return Response(update_data(obj,request.user),status=202)

