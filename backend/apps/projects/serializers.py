from apps.policy.service import active
from apps.people.serializers import person
from .models import ProjectMembership

def project_data(project):
    members = active(ProjectMembership.objects.filter(project=project,organization=project.organization,user__is_active=True)).select_related('user')
    return {'id':str(project.pk),'name':project.name,'description':project.description,'code':project.code,'color':project.color,'status':'Active' if project.is_active else 'Archived','members':[person(m.user) for m in members],'steward':project.steward.name}
