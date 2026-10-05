from django.db import models
from apps.core.models import TenantRecord

class WorkUpdate(TenantRecord):
    owner = models.ForeignKey('identity.User', on_delete=models.PROTECT)
    team = models.ForeignKey('projects.Team', on_delete=models.PROTECT)
    work_date = models.DateField()
    body = models.TextField(max_length=10000)
    status = models.CharField(max_length=30, choices=[(x,x) for x in ['draft','published','deletion_requested','deleted']], default='draft')
    visibility = models.CharField(max_length=20, choices=[('private','Private'),('lead_visible','Lead visible')], default='private')
    version = models.PositiveIntegerField(default=1)
    legal_hold = models.BooleanField(default=False)
    class Meta:
        indexes = [models.Index(fields=['organization','owner','status']), models.Index(fields=['organization','team','visibility'])]
        constraints = [models.CheckConstraint(condition=models.Q(visibility__in=['private','lead_visible']),name='valid_update_visibility'),models.CheckConstraint(condition=models.Q(status__in=['draft','published','deletion_requested','deleted']),name='valid_update_status')]

class UpdateRevision(TenantRecord):
    update = models.ForeignKey(WorkUpdate, on_delete=models.CASCADE, related_name='revisions')
    version = models.PositiveIntegerField()
    body = models.TextField()
    visibility = models.CharField(max_length=20)
    edited_by = models.ForeignKey('identity.User', on_delete=models.PROTECT)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['update','version'], name='unique_update_revision')]
