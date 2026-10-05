from django.db import models
from apps.core.models import TenantRecord, TimedRecord

class Team(TenantRecord):
    name = models.CharField(max_length=150)
    is_active = models.BooleanField(default=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['organization','name'],name='unique_team_name')]

class Project(TenantRecord):
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True, max_length=2000)
    code = models.CharField(max_length=8, default='PR')
    color = models.CharField(max_length=20, default='blue')
    is_active = models.BooleanField(default=True)
    steward = models.ForeignKey('identity.User', on_delete=models.PROTECT, related_name='stewarded_projects')
    class Meta:
        constraints = [models.UniqueConstraint(fields=['organization','name'],name='unique_project_name')]

class TeamMembership(TimedRecord):
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    user = models.ForeignKey('identity.User', on_delete=models.CASCADE)
    class Meta:
        indexes = [models.Index(fields=['organization','user','team'])]

class TeamLead(TimedRecord):
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    user = models.ForeignKey('identity.User', on_delete=models.CASCADE)
    class Meta:
        indexes = [models.Index(fields=['organization','user','team'])]

class ProjectMembership(TimedRecord):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    user = models.ForeignKey('identity.User', on_delete=models.CASCADE)
    class Meta:
        indexes = [models.Index(fields=['organization','user','project'])]
