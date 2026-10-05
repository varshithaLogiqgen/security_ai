from django.db import models
from apps.core.models import TenantRecord

class AuditEvent(TenantRecord):
    actor = models.ForeignKey('identity.User', null=True, blank=True, on_delete=models.PROTECT)
    action = models.CharField(max_length=80)
    target = models.CharField(max_length=100)
    decision = models.CharField(max_length=15)
    reason = models.CharField(max_length=60)
    policy_version = models.CharField(max_length=30)
    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValueError('Audit events are append-only.')
        return super().save(*args, **kwargs)
    def delete(self, *args, **kwargs):
        raise ValueError('Audit events are append-only.')
