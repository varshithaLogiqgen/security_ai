import json
import subprocess
import tarfile
import tempfile
from pathlib import Path
from datetime import datetime, timezone
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from apps.identity.models import Organization
from apps.documents.models import DocumentVersion
from apps.core.backup import EncryptedWriter, pg_environment


class Command(BaseCommand):
    help = 'Create an encrypted consistent database/private-files archive. Keys are never included.'

    def handle(self, *args, **options):
        if connection.vendor!='postgresql' or not settings.BACKUP_ENCRYPTION_KEY:
            raise CommandError('PostgreSQL and a separate BACKUP_ENCRYPTION_KEY are required.')
        root=settings.BACKUP_ROOT
        root.mkdir(parents=True,exist_ok=True,mode=0o700)
        name=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        pending=root/f'{name}.partial'
        target=root/f'{name}.backup'
        try:
            with tempfile.TemporaryDirectory() as temp, transaction.atomic():
                # Block application content writes while taking the dump and copying blobs.
                list(Organization.objects.select_for_update().order_by('pk').values_list('pk',flat=True))
                dump=Path(temp)/'database.dump'
                result=subprocess.run(['pg_dump','--format=custom','--no-owner','--no-acl','--file',str(dump)],env=pg_environment(settings.DATABASES['default']),capture_output=True,timeout=3600)
                if result.returncode: raise CommandError('pg_dump failed; check credentials and client/server compatibility.')
                with pending.open('xb') as output:
                    pending.chmod(0o600)
                    writer=EncryptedWriter(output,settings.BACKUP_ENCRYPTION_KEY)
                    with tarfile.open(fileobj=writer,mode='w|') as archive:
                        archive.add(dump,arcname='database.dump')
                        keys=DocumentVersion.objects.filter(document__purged_at__isnull=True).values_list('storage_key',flat=True).distinct()
                        for key in keys:
                            import uuid
                            if len(key)!=36 or not key.endswith('.enc'): raise CommandError('Invalid storage key.')
                            uuid.UUID(hex=key[:-4])
                            path=settings.PRIVATE_STORAGE_ROOT/key
                            if not path.is_file() or path.is_symlink(): raise CommandError('Referenced private file is missing or unsafe.')
                            archive.add(path,arcname=f'private/{key}',recursive=False)
                    writer.finish()
                pending.replace(target)
        except CommandError: raise
        except Exception: raise CommandError('Backup failed; no complete archive was published.') from None
        self.stdout.write(json.dumps({'archive':str(target),'status':'created','note':'Copy off-host and verify before considering this a recoverable backup.'}))
