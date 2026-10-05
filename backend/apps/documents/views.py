import io
from django.http import FileResponse
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, NotFound
from apps.core.api import endpoint,require,object_or_404,page,validated,version_check,Unavailable
from apps.audit.service import record
from apps.policy.service import visible_documents,authorize
from apps.projects.models import Project
from .models import Document, ProcessingJob
from .serializers import UploadInput,AccessInput,VersionUpload,document_data
from .services import stage,validate_grantees,replace_grants
from .storage import read_private

def document_list(request, project=None):
    rows=visible_documents(request.user).filter(title__icontains=request.query_params.get('q','')[:300])
    if project: rows=rows.filter(project=project)
    if request.query_params.get('project_id'):
        scoped_project=object_or_404(Project,request.query_params['project_id'],request.user)
        require(request.user,'project.read',scoped_project)
        rows=rows.filter(project=scoped_project)
    classification=request.query_params.get('classification')
    if classification: rows=rows.filter(classification=classification)
    rows=rows.select_related('project','uploader','current_version').order_by('-updated_at','id')
    return Response(page(request,[d for d in rows if authorize(request.user,'document.read',d).allow],lambda d:document_data(d,request.user)))

@endpoint(['GET','POST'])
def documents(request):
    if request.method=='GET': return document_list(request)
    data=validated(UploadInput,request)
    project=object_or_404(Project,data['project_id'],request.user)
    require(request.user,'document.upload',project)
    doc=Document.objects.create(organization=request.user.organization,project=project,uploader=request.user,title=data['title'])
    stage(doc,data['file'],request.user)
    record(request.user,'document.uploaded',doc.pk)
    return Response(document_data(doc,request.user),status=201)

@endpoint(['GET'])
def project_documents(request,pk):
    project=object_or_404(Project,pk,request.user)
    require(request.user,'project.read',project)
    return document_list(request,project)

@endpoint(['GET'])
def document(request,pk):
    doc=object_or_404(Document,pk,request.user)
    require(request.user,'document.read',doc)
    return Response(document_data(doc,request.user))

@endpoint(['POST'])
def publish(request,pk):
    doc=object_or_404(Document,pk,request.user)
    require(request.user,'document.manage',doc)
    version_check(request,doc)
    data=validated(AccessInput,request)
    if doc.status!='unpublished' or not ProcessingJob.objects.filter(version=doc.current_version,status='completed').exists(): raise ValidationError('The document has not completed validation.')
    if doc.ever_published and doc.classification=='restricted' and data['classification']=='project': raise ValidationError('Widening requires independent steward approval.')
    users=validate_grantees(request.user,doc,data['grants'])
    if data['classification']=='restricted' and not users: raise ValidationError('Choose at least one project member.')
    replace_grants(doc,users,request.user)
    doc.classification=data['classification']
    doc.status='published'
    doc.ever_published=True
    doc.version+=1
    doc.save()
    record(request.user,'document.published',doc.pk)
    return Response(document_data(doc,request.user))

@endpoint(['PATCH'])
def access(request,pk):
    from apps.administration.services import widening_request,approval_data
    doc=object_or_404(Document,pk,request.user)
    require(request.user,'document.manage',doc)
    version_check(request,doc)
    data=validated(AccessInput,request)
    users=validate_grantees(request.user,doc,data['grants'])
    if doc.ever_published and doc.classification=='restricted' and data['classification']=='project':
        approval=widening_request(request.user,doc)
        return Response(approval_data(approval,request.user),status=202)
    if data['classification']=='restricted' and not users: raise ValidationError('Choose at least one project member.')
    if doc.status not in {'unpublished','published'}: raise ValidationError('Wait until file validation has completed.')
    replace_grants(doc,users,request.user)
    doc.classification=data['classification']
    doc.status='unpublished'
    doc.version+=1
    doc.save()
    record(request.user,'document.access_changed',doc.pk)
    return Response(document_data(doc,request.user))

@endpoint(['POST'])
def versions(request,pk):
    doc=object_or_404(Document,pk,request.user)
    require(request.user,'document.manage',doc)
    version_check(request,doc)
    data=validated(VersionUpload,request)
    doc.version+=1
    stage(doc,data['file'],request.user)
    record(request.user,'document.version_staged',doc.pk)
    return Response(document_data(doc,request.user),status=201)

@endpoint(['POST'])
def request_deletion(request,pk):
    from apps.administration.services import removal_request
    doc=object_or_404(Document,pk,request.user)
    require(request.user,'document.manage',doc)
    version_check(request,doc)
    removal_request(request.user,doc,'document_delete')
    return Response(document_data(doc,request.user),status=202)

@endpoint(['GET'])
def download(request,pk):
    doc=object_or_404(Document,pk,request.user)
    require(request.user,'document.download',doc)
    current=doc.current_version
    if not current or not ProcessingJob.objects.filter(version=current,status='completed').exists(): raise NotFound()
    try: data=read_private(current.storage_key)
    except Exception: raise Unavailable()
    require(request.user,'document.download',doc)
    record(request.user,'document.download',doc.pk)
    response=FileResponse(io.BytesIO(data),as_attachment=True,filename=f'document-{doc.pk}.{current.file_type.lower()}',content_type=current.mime)
    return response
