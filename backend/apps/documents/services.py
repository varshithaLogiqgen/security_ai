import hashlib
from django.conf import settings
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from apps.core.api import object_or_404
from apps.identity.models import User
from apps.policy.service import member
from .models import DocumentVersion, DocumentGrant, ProcessingJob
from .storage import write_private

def stage(document,file,user):
    extension=file.name.rsplit('.',1)[-1].upper()
    if extension not in {'PDF','DOCX','TXT'} or file.size>settings.MAX_FILE_SIZE or file.size==0:
        raise ValidationError('Choose a PDF, DOCX, or TXT file up to 10 MB.')
    data=file.read(settings.MAX_FILE_SIZE+1)
    if len(data)>settings.MAX_FILE_SIZE: raise ValidationError('The file is too large.')
    mime={'PDF':'application/pdf','DOCX':'application/vnd.openxmlformats-officedocument.wordprocessingml.document','TXT':'text/plain'}[extension]
    if extension=='PDF' and not data.startswith(b'%PDF-'): raise ValidationError('File type does not match its contents.')
    if extension=='DOCX' and not data.startswith(b'PK'): raise ValidationError('File type does not match its contents.')
    number=(document.versions.order_by('-version_no').values_list('version_no',flat=True).first() or 0)+1
    version=DocumentVersion.objects.create(organization=user.organization,document=document,version_no=number,storage_key=write_private(data),sha256=hashlib.sha256(data).hexdigest(),mime=mime,file_type=extension,byte_size=len(data),created_by=user)
    document.current_version=version
    document.status='processing'
    document.save()
    ProcessingJob.objects.create(organization=user.organization,version=version)
    return version

def validate_grantees(user,document,ids):
    if len(ids)!=len(set(ids)): raise ValidationError('Duplicate grants are not allowed.')
    users=[]
    for pk in ids:
        grantee=object_or_404(User,pk,user)
        if not grantee.is_active or not member(grantee,document.project): raise ValidationError('Grantees must be active members of this project.')
        users.append(grantee)
    return users

def replace_grants(document,users,actor):
    document.grants.filter(revoked_at__isnull=True).update(revoked_at=timezone.now())
    for user in users:
        DocumentGrant.objects.create(organization=document.organization,document=document,grantee=user,assigned_by=actor)
