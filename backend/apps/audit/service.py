from .models import AuditEvent
from apps.policy.service import POLICY_VERSION

def record(user, action, target='', decision='allow', reason='allowed'):
    # Callers pass only IDs and static codes. Never source content or private prompts.
    return AuditEvent.objects.create(organization=user.organization, actor=user, action=action[:80], target=str(target or "none")[:100], decision=decision, reason=reason[:60], policy_version=POLICY_VERSION)

