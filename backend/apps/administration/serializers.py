from rest_framework import serializers

class InviteInput(serializers.Serializer):
    email=serializers.EmailField()
    reason=serializers.CharField(min_length=10,max_length=1000)

class TeamInput(serializers.Serializer):
    name=serializers.CharField(max_length=150)
    reason=serializers.CharField(min_length=10,max_length=1000)

class ProjectInput(TeamInput):
    steward_user_id=serializers.UUIDField()
    description=serializers.CharField(max_length=2000,required=False,allow_blank=True)

class AccessRequestInput(serializers.Serializer):
    target_user_id=serializers.UUIDField()
    action=serializers.ChoiceField(choices=['project_membership','team_membership','team_lead'])
    operation=serializers.ChoiceField(choices=['assign','revoke'])
    scope_id=serializers.UUIDField()
    expires_at=serializers.DateTimeField()
    reason=serializers.CharField(min_length=10,max_length=1000)

class ReviewInput(serializers.Serializer):
    decision=serializers.ChoiceField(choices=['approve','reject'])
    reason=serializers.CharField(min_length=10,max_length=1000)

class ReasonInput(serializers.Serializer):
    reason=serializers.CharField(min_length=10,max_length=1000)
