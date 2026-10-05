import hashlib
from datetime import timedelta
from unittest.mock import Mock, patch

from django.test import TestCase, override_settings
from django.utils import timezone
from apps.administration.models import Invitation
from apps.identity.models import Organization, User, UserRole


@override_settings(OIDC_ISSUER='https://identity.example.test', OIDC_CLIENT_ID='pilot')
class InvitationTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name='Pilot')
        self.admin = User.objects.create_user(username='admin', organization=self.org, name='Admin', email='admin@example.test')
        self.invite = Invitation.objects.create(
            organization=self.org, invited_by=self.admin, email='new@example.test',
            token_hash=hashlib.sha256(b'example-token').hexdigest(),
            expires_at=timezone.now() + timedelta(days=1),
        )

    def callback(self, **overrides):
        claims = dict(iss='https://identity.example.test', sub='verified-subject', email='new@example.test', email_verified=True)
        claims.update(overrides)
        oauth = Mock()
        oauth.authorize_access_token.return_value = {'userinfo': claims}
        with patch('apps.identity.views.oauth_client', return_value=oauth):
            return self.client.get('/api/v1/auth/callback')

    def test_verified_invitation_creates_basic_account_once(self):
        self.assertEqual(self.client.get('/api/v1/auth/accept?token=example-token').status_code, 302)
        self.assertEqual(self.callback().status_code, 302)
        user = User.objects.get(oidc_subject='verified-subject')
        self.assertEqual(user.organization_id, self.org.pk)
        self.assertFalse(user.has_usable_password())
        self.assertFalse(UserRole.objects.filter(user=user).exists())
        self.invite.refresh_from_db()
        self.assertIsNotNone(self.invite.accepted_at)
        self.assertEqual(self.client.get('/api/v1/auth/accept?token=example-token').status_code, 404)

    def test_unverified_or_mismatched_identity_cannot_redeem(self):
        self.client.get('/api/v1/auth/accept?token=example-token')
        for overrides in [{'email_verified': False}, {'email': 'other@example.test'}, {'iss': 'https://evil.example.test'}]:
            self.assertEqual(self.callback(**overrides).status_code, 401)
        self.assertFalse(User.objects.filter(oidc_subject='verified-subject').exists())
        self.invite.refresh_from_db()
        self.assertIsNone(self.invite.accepted_at)

    def test_expired_invitation_is_unavailable(self):
        self.invite.expires_at = timezone.now() - timedelta(seconds=1)
        self.invite.save()
        self.assertEqual(self.client.get('/api/v1/auth/accept?token=example-token').status_code, 404)
