import uuid
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

class Record(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    class Meta:
        abstract = True

class TenantRecord(Record):
    organization = models.ForeignKey('identity.Organization', on_delete=models.PROTECT)
    class Meta:
        abstract = True
    def clean(self):
        super().clean()
        for field in self._meta.fields:
            if isinstance(field, models.ForeignKey) and field.name != 'organization' and getattr(self, field.attname):
                related = getattr(self, field.name)
                if hasattr(related, 'organization_id') and related.organization_id != self.organization_id:
                    raise ValidationError('Relationships must belong to the same organization.')
    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

class TimedRecord(TenantRecord):
    valid_from = models.DateTimeField(default=timezone.now)
    valid_to = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    assigned_by = models.ForeignKey('identity.User', on_delete=models.PROTECT, related_name='+', null=True, blank=True)
    class Meta:
        abstract = True
    def clean(self):
        super().clean()
        if self.valid_to and self.valid_to <= self.valid_from:
            raise ValidationError('Expiry must be later than the start.')

class IdempotencyRecord(TenantRecord):
    user = models.ForeignKey('identity.User', on_delete=models.CASCADE)
    key = models.CharField(max_length=100)
    fingerprint = models.CharField(max_length=64)
    status = models.PositiveSmallIntegerField(default=0)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['user', 'key'], name='unique_idempotency_key')]

class RateBucket(models.Model):
    key = models.CharField(primary_key=True, max_length=128)
    count = models.PositiveIntegerField(default=0)
    expires_at = models.DateTimeField()
