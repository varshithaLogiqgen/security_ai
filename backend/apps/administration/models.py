from django.db import models
from apps.core.models import TenantRecord

class Invitation(TenantRecord):
    email = models.EmailField()
    invited_by = models.ForeignKey('identity.User', on_delete=models.PROTECT)
    token_hash = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(null=True, blank=True)

class Approval(TenantRecord):
    requester = models.ForeignKey('identity.User', on_delete=models.PROTECT, related_name='+')
    kind = models.CharField(max_length=30)
    target_user = models.ForeignKey('identity.User', null=True, blank=True, on_delete=models.PROTECT, related_name='+')
    scope_id = models.UUIDField()
    reason = models.TextField(max_length=1000)
    payload = models.JSONField(default=dict)
    status = models.CharField(max_length=20, default='pending')
    expires_at = models.DateTimeField()

class ApprovalReview(TenantRecord):
    approval = models.ForeignKey(Approval, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey('identity.User', on_delete=models.PROTECT)
    role = models.CharField(max_length=20)
    decision = models.CharField(max_length=20)
    reason = models.CharField(max_length=1000)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['approval','reviewer'],name='one_review_per_approver')]
