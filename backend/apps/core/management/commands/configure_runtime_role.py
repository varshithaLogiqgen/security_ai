from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction


class Command(BaseCommand):
    help = 'Grant the separate secureai_app runtime role DML only; run with the migration owner.'

    @transaction.atomic
    def handle(self, *args, **options):
        if connection.vendor != 'postgresql': raise CommandError('PostgreSQL required.')
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM pg_roles WHERE rolname='secureai_app' AND NOT rolsuper AND NOT rolcreatedb AND NOT rolcreaterole")
            if not cursor.fetchone(): raise CommandError('Create the unprivileged secureai_app role first.')
            cursor.execute('GRANT USAGE ON SCHEMA public TO secureai_app')
            cursor.execute('GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO secureai_app')
            cursor.execute('GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO secureai_app')
            for table in ('audit_auditevent', 'documents_documentversion', 'work_updates_updaterevision', 'django_migrations'):
                cursor.execute(f'REVOKE UPDATE, DELETE ON {table} FROM secureai_app')
            cursor.execute('REVOKE INSERT ON django_migrations FROM secureai_app')
        self.stdout.write('Runtime grants applied. Schema ownership remains with the migration role.')
