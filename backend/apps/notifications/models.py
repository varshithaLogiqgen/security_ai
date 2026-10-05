from django.db import models
from apps.core.models import TenantRecord

class Notification(TenantRecord):
    user = models.ForeignKey('identity.User', on_delete=models.CASCADE)
    message = models.CharField(max_length=200)
    read_at = models.DateTimeField(null=True, blank=True)
