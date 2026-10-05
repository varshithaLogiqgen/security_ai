import json
import socket
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
import requests
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from config.production import validate_production
from apps.documents.processing import scan, ProcessingError


class Command(BaseCommand):
    help = 'Check production configuration, database role, OIDC, scanner and model using synthetic probes only.'

    def handle(self, *args, **options):
        failures = []
        checks = [
            ('configuration', self.configuration), ('database', self.database),
            ('oidc_discovery', self.oidc), ('malware_scanner', self.scanner),
            ('ai_model', self.provider),
        ]
        for name, check in checks:
            try:
                check()
                self.stdout.write(json.dumps({'check':name, 'status':'passed'}))
            except Exception:
                failures.append(name)
                self.stdout.write(json.dumps({'check':name, 'status':'failed'}))
        if failures: raise CommandError('Production verification failed: ' + ', '.join(failures))

    def configuration(self):
        if settings.DEBUG or settings.SYNTHETIC_MODE: raise ValueError()
        validate_production({name:getattr(settings,name) for name in dir(settings) if name.isupper()})
        call_command('check', deploy=True, fail_level='WARNING', verbosity=0)

    def database(self):
        if connection.vendor != 'postgresql': raise ValueError()
        call_command('runtime_health', verbosity=0)
        with connection.cursor() as cursor:
            cursor.execute('SELECT rolsuper, rolcreatedb, rolcreaterole FROM pg_roles WHERE rolname=current_user')
            if any(cursor.fetchone()): raise ValueError()
            cursor.execute("SELECT count(*) FROM pg_tables WHERE schemaname='public' AND tableowner=current_user")
            if cursor.fetchone()[0]: raise ValueError('Runtime user owns schema')
            cursor.execute("SELECT count(*) FROM pg_trigger WHERE NOT tgisinternal AND tgname LIKE '%tenant_guard'")
            if cursor.fetchone()[0] < 20: raise ValueError('Missing tenant guards')

    def oidc(self):
        response = requests.get(settings.OIDC_ISSUER.rstrip('/')+'/.well-known/openid-configuration', timeout=10, allow_redirects=False)
        response.raise_for_status()
        data = response.json()
        if data['issuer'] != settings.OIDC_ISSUER: raise ValueError()
        for field in ('authorization_endpoint','token_endpoint','jwks_uri'):
            if not data[field].startswith('https://'): raise ValueError()
        if 'code' not in data.get('response_types_supported', []): raise ValueError()
        keys = requests.get(data['jwks_uri'], timeout=10, allow_redirects=False)
        keys.raise_for_status()
        if not keys.json().get('keys'): raise ValueError()

    def scanner(self):
        if settings.SCANNER_MODE != 'clamav': raise ValueError()
        with socket.create_connection((settings.CLAMAV_HOST,settings.CLAMAV_PORT),timeout=10) as client:
            client.sendall(b'zVERSION\0')
            version = client.recv(4096).decode().strip('\0\n')
        # clamd returns engine/signature version/signature timestamp.
        timestamp = datetime.strptime(version.split('/')[-1], '%a %b %d %H:%M:%S %Y').replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc)-timestamp > timedelta(hours=settings.CLAMAV_MAX_SIGNATURE_AGE_HOURS): raise ValueError()
        scan(b'Synthetic clean scanner readiness probe.')
        eicar = b'X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*'
        try: scan(eicar)
        except ProcessingError as exc:
            if str(exc) == 'malware_detected': return
        raise ValueError('Scanner did not detect standard test signature')

    def provider(self):
        from apps.assistant.providers import OllamaProvider
        from types import SimpleNamespace
        evidence = [SimpleNamespace(title='Synthetic verification',excerpt='The synthetic verification color is blue.')]
        result = OllamaProvider().answer('What is the synthetic verification color?',evidence)
        if not isinstance(result,dict) or not isinstance(result.get('answer'),str) or not result['answer'].strip() or result.get('citations') != [0]:
            raise ValueError('Provider contract failed')
