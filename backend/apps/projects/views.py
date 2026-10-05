from rest_framework.response import Response
from apps.core.api import endpoint, object_or_404, require, page
from apps.policy.service import active, authorize
from .models import Project, ProjectMembership, TeamMembership
from .serializers import project_data

@endpoint(['GET'])
def projects(request):
    ids = active(ProjectMembership.objects.filter(user=request.user,organization=request.user.organization)).values('project_id')
    rows = Project.objects.filter(organization=request.user.organization,pk__in=ids,is_active=True,name__icontains=request.query_params.get('q','')[:300]).order_by('name','id')
    return Response(page(request,[p for p in rows if authorize(request.user,'project.read',p).allow],project_data))

@endpoint(['GET'])
def project(request,pk):
    obj = object_or_404(Project,pk,request.user)
    require(request.user,'project.read',obj)
    return Response(project_data(obj))

@endpoint(['GET'])
def teams(request):
    rows = active(TeamMembership.objects.filter(user=request.user,organization=request.user.organization,team__is_active=True)).select_related('team')
    return Response(page(request,rows,lambda r:{'id':str(r.team_id),'name':r.team.name}))
