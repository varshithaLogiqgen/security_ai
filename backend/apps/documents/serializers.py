from rest_framework import serializers
from apps.core.api import VersionInput
from apps.policy.service import authorize, active

class UploadInput(serializers.Serializer):
    file = serializers.FileField()
    title = serializers.CharField(max_length=200)
    project_id = serializers.UUIDField()

class AccessInput(VersionInput):
    classification = serializers.ChoiceField(choices=['project','restricted'])
    grants = serializers.ListField(child=serializers.UUIDField(),max_length=200)

class VersionUpload(serializers.Serializer):
    file = serializers.FileField()

def document_data(doc,user):
    current=doc.current_version
    can_manage=authorize(user,'document.manage',doc).allow
    return {'id':str(doc.pk),'title':doc.title,'project_id':str(doc.project_id),'project_name':doc.project.name,'uploader_id':str(doc.uploader_id),'uploader_name':doc.uploader.name,'classification':doc.classification,'status':doc.status,'version':doc.version,'file_version':current.version_no if current else 0,'type':current.file_type if current else 'TXT','size':f'{max(1,round(current.byte_size/1024)) if current else 0} KB','updated_at':doc.updated_at.isoformat(),'grants':[str(g.grantee_id) for g in active(doc.grants.all())] if can_manage else [],'can_manage':can_manage}
