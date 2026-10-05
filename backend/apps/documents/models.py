from django.db import models
from apps.core.models import TenantRecord, TimedRecord

class Document(TenantRecord):
    title = models.CharField(max_length=200)
    project = models.ForeignKey('projects.Project', on_delete=models.PROTECT)
    uploader = models.ForeignKey('identity.User', on_delete=models.PROTECT)
    classification = models.CharField(max_length=20, choices=[('project','Project'),('restricted','Restricted')], default='restricted')
    status = models.CharField(max_length=30, default='processing', choices=[(s,s) for s in ['processing','unpublished','published','failed','quarantined','deletion_requested','deleted']])
    version = models.PositiveIntegerField(default=1)
    current_version = models.ForeignKey('DocumentVersion', null=True, blank=True, on_delete=models.PROTECT, related_name='+')
    ever_published = models.BooleanField(default=False)
    legal_hold = models.BooleanField(default=False)
    purged_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        constraints = [models.CheckConstraint(condition=models.Q(classification__in=['project','restricted']),name='valid_document_classification'),models.CheckConstraint(condition=models.Q(status__in=['processing','unpublished','published','failed','quarantined','deletion_requested','deleted']),name='valid_document_status')]
        indexes = [models.Index(fields=['organization','project','status'])]
    def clean(self):
        super().clean()
        if self.current_version_id and self.current_version.document_id != self.id:
            from django.core.exceptions import ValidationError
            raise ValidationError('Version must belong to this document.')

class DocumentVersion(TenantRecord):
    document = models.ForeignKey(Document, on_delete=models.PROTECT, related_name='versions')
    version_no = models.PositiveIntegerField()
    storage_key = models.CharField(max_length=100)
    sha256 = models.CharField(max_length=64)
    mime = models.CharField(max_length=100)
    file_type = models.CharField(max_length=5)
    byte_size = models.PositiveIntegerField()
    created_by = models.ForeignKey('identity.User', on_delete=models.PROTECT)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['document','version_no'],name='unique_document_version')]

class ProcessingJob(TenantRecord):
    version = models.OneToOneField(DocumentVersion, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, default='pending')
    error_code = models.CharField(max_length=40, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

class DocumentGrant(TimedRecord):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='grants')
    grantee = models.ForeignKey('identity.User', on_delete=models.CASCADE)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['document','grantee'],condition=models.Q(revoked_at__isnull=True),name='unique_unrevoked_grant')]

class DocumentChunk(TenantRecord):
    version = models.ForeignKey(DocumentVersion, on_delete=models.CASCADE, related_name='chunks')
    ordinal = models.PositiveIntegerField()
    text = models.TextField()
    locator = models.CharField(max_length=100)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['version','ordinal'],name='unique_chunk_ordinal')]
