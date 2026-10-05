from rest_framework import serializers
from apps.core.api import VersionInput

class CreateUpdate(serializers.Serializer):
    team_id = serializers.UUIDField()
    work_date = serializers.DateField()
    body = serializers.CharField(min_length=10,max_length=10000)

class EditUpdate(VersionInput):
    team_id = serializers.UUIDField(required=False)
    work_date = serializers.DateField(required=False)
    body = serializers.CharField(min_length=10,max_length=10000,required=False)
    visibility = serializers.ChoiceField(choices=['private','lead_visible'],required=False)

class PublishUpdate(VersionInput):
    visibility = serializers.ChoiceField(choices=['private','lead_visible'])

def update_data(obj,user):
    revisions = obj.revisions.order_by('-version') if obj.owner_id == user.pk else []
    return {'id':str(obj.pk),'owner_id':str(obj.owner_id),'owner_name':obj.owner.name,'team_id':str(obj.team_id),'team_name':obj.team.name,'work_date':obj.work_date.isoformat(),'body':obj.body,'status':obj.status,'visibility':obj.visibility,'version':obj.version,'revisions':[{'version':r.version,'body':r.body,'date':r.created_at.isoformat()} for r in revisions]}
