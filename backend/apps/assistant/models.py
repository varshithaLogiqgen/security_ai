from django.db import models
from apps.core.models import TenantRecord

class Conversation(TenantRecord):
    owner = models.ForeignKey('identity.User', on_delete=models.CASCADE)
    title = models.CharField(max_length=60, default='New conversation')
    is_deleted = models.BooleanField(default=False)
    legal_hold = models.BooleanField(default=False)

class Message(TenantRecord):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    question = models.TextField(max_length=4000)
    answer = models.TextField(blank=True)
    state = models.CharField(max_length=25, default='insufficient')
    policy_version = models.CharField(max_length=30)

class AnswerSource(TenantRecord):
    is_citation = models.BooleanField(default=True)
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='sources')
    source_type = models.CharField(max_length=20)
    source_id = models.UUIDField()
    version = models.PositiveIntegerField()
    locator = models.CharField(max_length=100)
