from django.db import models
from apps.core.models import TenantRecord

class PersonalProfile(TenantRecord):
    user = models.OneToOneField('identity.User', on_delete=models.CASCADE)
    encrypted_data = models.TextField()
    updated_at = models.DateTimeField(auto_now=True)
