from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.db.migrations.executor import MigrationExecutor


class Command(BaseCommand):
    help = 'Read-only database and migration health check; no credentials in output.'

    def handle(self, *args, **options):
        try:
            with connection.cursor() as cursor: cursor.execute('SELECT 1')
            executor = MigrationExecutor(connection)
            if executor.migration_plan(executor.loader.graph.leaf_nodes()):
                raise CommandError('Pending database migrations.')
        except CommandError: raise
        except Exception: raise CommandError('Database health check failed.') from None
        self.stdout.write('Database reachable; migrations current.')
