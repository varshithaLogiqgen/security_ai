import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from apps.core.models import Record, TimedRecord

class Organization(Record):
    name = models.CharField(max_length=150)
    is_active = models.BooleanField(default=True)
    def __str__(self): return self.name

class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT)
    name = models.CharField(max_length=150)
    email = models.EmailField()
    title = models.CharField(max_length=150, blank=True)
    directory_team = models.CharField(max_length=150, blank=True)
    bio = models.TextField(blank=True, max_length=1000)
    profile_version = models.PositiveIntegerField(default=1)
    oidc_subject = models.CharField(max_length=255, null=True, blank=True, unique=True)
    oidc_issuer = models.CharField(max_length=500, blank=True)
    session_version = models.PositiveIntegerField(default=1)
    REQUIRED_FIELDS = ['organization_id', 'name', 'email']
    class Meta:
        constraints = [models.UniqueConstraint(fields=['organization','email'], name='unique_org_email')]

class UserRole(TimedRecord):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=30, choices=[('admin','Organization admin'),('audit','Security reviewer'),('retention','Retention steward')])
    class Meta:
        indexes = [models.Index(fields=['organization','user','role'])]
