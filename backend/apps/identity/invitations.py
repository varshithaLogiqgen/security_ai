import hashlib
import uuid

from django.utils import timezone
from apps.administration.models import Invitation
from apps.identity.models import Organization, User


def redeem(request, claims):
    """Called inside the callback transaction, after OIDC token verification."""
    digest = request.session.get('invitation_hash')
    if not digest or claims.get('email_verified') is not True:
        raise ValueError('Verified invitation required')
    invitation = Invitation.objects.select_related('organization').filter(
        token_hash=digest, accepted_at__isnull=True,
        expires_at__gt=timezone.now(), organization__is_active=True,
    ).first()
    if not invitation:
        raise ValueError('Invitation unavailable')
    Organization.objects.select_for_update().get(pk=invitation.organization_id)
    invitation.refresh_from_db()
    if invitation.accepted_at or invitation.expires_at <= timezone.now():
        raise ValueError('Invitation unavailable')
    email = str(claims.get('email', '')).lower()
    if email != invitation.email.lower():
        raise ValueError('Invitation identity mismatch')
    # Existing accounts must be bound by an operator, never linked by email alone.
    if User.objects.filter(organization=invitation.organization, email__iexact=email).exists():
        raise ValueError('Account already exists')
    user = User.objects.create_user(
        username=f'oidc-{uuid.uuid4().hex}', organization=invitation.organization,
        email=email, name=str(claims.get('name') or email)[:150],
        oidc_subject=claims['sub'], oidc_issuer=claims['iss'],
    )
    invitation.accepted_at = timezone.now()
    invitation.save()
    request.session.pop('invitation_hash', None)
    return user


def token_digest(token):
    return hashlib.sha256(token.encode()).hexdigest()
