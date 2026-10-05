import subprocess
import tarfile
import tempfile
import uuid
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from apps.core.backup import decrypt_archive


class Command(BaseCommand):
    help='Authenticate and inspect an encrypted backup. Optionally extract into a NEW recovery directory; never touches the running database.'

    def add_arguments(self,parser):
        parser.add_argument('archive')
        parser.add_argument('--extract-to')

    def handle(self,*args,**options):
        destination=Path(options['extract_to']).resolve() if options['extract_to'] else None
        if destination and destination.exists(): raise CommandError('Recovery directory must not already exist.')
        try:
            with tempfile.TemporaryDirectory() as temp:
                decrypted=Path(temp)/'archive.tar'
                with Path(options['archive']).open('rb') as source, decrypted.open('wb') as output:
                    decrypt_archive(source,output,settings.BACKUP_ENCRYPTION_KEY)
                seen=set()
                with tarfile.open(decrypted,'r:') as archive:
                    for member in archive:
                        if not member.isfile() or member.name in seen: raise ValueError()
                        seen.add(member.name)
                        if member.name!='database.dump':
                            if not member.name.startswith('private/') or len(member.name)!=44 or not member.name.endswith('.enc'): raise ValueError()
                            uuid.UUID(hex=member.name[8:-4])
                    if 'database.dump' not in seen: raise ValueError()
                    # Inspect the actual pg_dump structure, not just archive encryption.
                    database=Path(temp)/'database.dump'
                    with database.open('wb') as output:
                        import shutil
                        shutil.copyfileobj(archive.extractfile('database.dump'),output)
                    result=subprocess.run(['pg_restore','--list',str(database)],capture_output=True,timeout=60)
                    if result.returncode: raise ValueError()
                    if destination:
                        destination.mkdir(parents=True,mode=0o700)
                        archive.extractall(destination,filter='data')
        except Exception: raise CommandError('Backup verification failed. No running database was modified.') from None
        self.stdout.write('Backup authenticated and database archive readable. A restore drill is still required.')
