from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from apps.identity.models import Organization, User, UserRole
from apps.audit.service import record


class Command(BaseCommand):
    help = 'Bootstrap a new organization and its initial OIDC administrator. Operator-only.'

    def add_arguments(self, parser):
        for name in ['organization', 'username', 'name', 'email', 'subject']:
            parser.add_argument(f'--{name}', required=True)

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.OIDC_ISSUER:
            raise CommandError('Configure the trusted OIDC_ISSUER first.')
        if Organization.objects.filter(name=options['organization']).exists():
            raise CommandError('Organization already exists; bootstrap cannot change existing access.')
        if User.objects.filter(username=options['username']).exists() or User.objects.filter(oidc_subject=options['subject']).exists():
            raise CommandError('Identity already exists.')
        org = Organization.objects.create(name=options['organization'])
        user = User.objects.create_user(
            organization=org, username=options['username'], name=options['name'],
            email=options['email'].lower(), oidc_subject=options['subject'],
            oidc_issuer=settings.OIDC_ISSUER,
        )
        user.full_clean()
        UserRole.objects.create(organization=org, user=user, role='admin')
        record(user, 'admin.organization.bootstrapped', org.pk)
        self.stdout.write(f'Organization {org.pk} created with administrator {user.pk}.')
