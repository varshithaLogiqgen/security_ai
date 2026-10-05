from rest_framework.response import Response
from apps.core.api import endpoint
from apps.policy.service import visible_documents,visible_updates,active
from apps.projects.models import ProjectMembership

@endpoint(['GET'])
def overview(request):
    return Response({'projects':active(ProjectMembership.objects.filter(user=request.user,organization=request.user.organization,project__is_active=True)).values('project_id').distinct().count(),'updates':visible_updates(request.user).filter(owner=request.user).count(),'documents':visible_documents(request.user).count()})
