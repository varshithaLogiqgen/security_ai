import io
import os
import tempfile
from pathlib import Path
from datetime import timedelta
from unittest.mock import patch
from cryptography.fernet import Fernet, InvalidToken
from django.core.exceptions import ImproperlyConfigured
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase, TestCase, override_settings
from django.utils import timezone
from config.environment import value
from config.production import validate_production
from apps.core.backup import EncryptedWriter, decrypt_archive
from apps.identity.models import Organization, User
from apps.assistant.models import Conversation, Message
from django.db import connection, transaction
from unittest import skipUnless


class ProductionConfigTests(SimpleTestCase):
    def test_complete_configuration_and_insecure_provider_rejection(self):
        config=dict(OIDC_ISSUER='https://id.example.test',FRONTEND_URL='https://work.example.test',OIDC_CLIENT_ID='client',OIDC_CLIENT_SECRET='secret',AI_APPROVAL_REFERENCE='test-approval',RETENTION_POLICY_REFERENCE='test-policy',CHAT_RETENTION_DAYS=30,DELETED_FILE_RETENTION_DAYS=30,AUDIT_RETENTION_DAYS=365,BACKUP_RETENTION_DAYS=30,DATA_ENCRYPTION_KEY=Fernet.generate_key().decode(),BACKUP_ENCRYPTION_KEY=Fernet.generate_key().decode(),SECRET_KEY='random-secret-for-validation-only-'*3,SCANNER_MODE='clamav',AI_PROVIDER_APPROVED=True,AI_ADAPTER='apps.assistant.providers.OllamaProvider',OLLAMA_URL='http://ollama:11434',OLLAMA_MODEL='approved-test-model',ALLOWED_HOSTS=['work.example.test'],CSRF_TRUSTED_ORIGINS=['https://work.example.test'])
        validate_production(config)
        config['OLLAMA_URL']='http://external.example.test'
        with self.assertRaises(ImproperlyConfigured): validate_production(config)

    def test_clamav_errors_fail_closed(self):
        from apps.documents.processing import scan, ProcessingError
        for reply in (b'stream: ERROR\0',b'stream: NOT OK\0',b'',b'stream: signature FOUND\0'):
            with override_settings(SCANNER_MODE='clamav'), patch('apps.documents.processing.socket.create_connection') as connect:
                connect.return_value.__enter__.return_value.recv.return_value=reply
                with self.assertRaises(ProcessingError): scan(b'synthetic content')

    def test_missing_production_choices_fail_closed(self):
        with self.assertRaises(ImproperlyConfigured): validate_production({})

    def test_secret_file_and_conflicting_sources(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'secret'
            path.write_text('secret-value\n')
            with patch.dict(os.environ, {'EXAMPLE_SECRET_FILE':str(path)}, clear=True):
                self.assertEqual(value('EXAMPLE_SECRET'),'secret-value')
                os.environ['EXAMPLE_SECRET']='conflict'
                with self.assertRaises(ImproperlyConfigured): value('EXAMPLE_SECRET')

    def test_backup_roundtrip_and_truncation(self):
        key=Fernet.generate_key().decode()
        output=io.BytesIO()
        writer=EncryptedWriter(output,key)
        original=b'Private backup data.'*100000
        writer.write(original)
        writer.finish()
        encoded=output.getvalue()
        self.assertNotIn(b'Private backup data.',encoded)
        restored=io.BytesIO()
        decrypt_archive(io.BytesIO(encoded),restored,key)
        self.assertEqual(restored.getvalue(),original)
        for bad in (encoded[:-10],encoded+b'extra',encoded[:100]+b'tamper'+encoded[106:]):
            with self.assertRaises((ValueError,InvalidToken)):
                decrypt_archive(io.BytesIO(bad),io.BytesIO(),key)

    def test_backup_wrong_key_rejected(self):
        output=io.BytesIO()
        writer=EncryptedWriter(output,Fernet.generate_key().decode())
        writer.write(b'content');writer.finish()
        with self.assertRaises(InvalidToken): decrypt_archive(io.BytesIO(output.getvalue()),io.BytesIO(),Fernet.generate_key().decode())


@override_settings(RETENTION_POLICY_REFERENCE='test-policy',CHAT_RETENTION_DAYS=30,DELETED_FILE_RETENTION_DAYS=30,AUDIT_RETENTION_DAYS=365)
class RetentionTests(TestCase):
    def setUp(self):
        org=Organization.objects.create(name='Retention test')
        self.user=User.objects.create_user(username='retention-test',organization=org,name='Test',email='test@example.test')

    def chat(self,held=False,recent=False):
        chat=Conversation.objects.create(organization=self.user.organization,owner=self.user,legal_hold=held,created_at=timezone.now()-timedelta(days=40))
        Message.objects.create(organization=self.user.organization,conversation=chat,question='Synthetic question',answer='Synthetic answer',policy_version='test',created_at=timezone.now()-timedelta(days=1 if recent else 40))
        return chat

    def test_dry_run_does_not_delete(self):
        chat=self.chat()
        call_command('enforce_retention',stdout=io.StringIO())
        self.assertTrue(Conversation.objects.filter(pk=chat.pk).exists())

    def test_expired_chat_purged_but_hold_and_active_chats_preserved(self):
        expired=self.chat();held=self.chat(held=True);active=self.chat(recent=True)
        call_command('enforce_retention',apply=True,stdout=io.StringIO())
        self.assertFalse(Conversation.objects.filter(pk=expired.pk).exists())
        self.assertTrue(Conversation.objects.filter(pk=held.pk).exists())
        self.assertTrue(Conversation.objects.filter(pk=active.pk).exists())

    @override_settings(RETENTION_POLICY_REFERENCE='')
    def test_unapproved_retention_cannot_run(self):
        with self.assertRaises(CommandError): call_command('enforce_retention',apply=True)

    def test_file_purge_preserves_metadata_and_legal_hold(self):
        from apps.projects.models import Project
        from apps.documents.models import Document, DocumentVersion
        from apps.documents.storage import write_private
        project=Project.objects.create(organization=self.user.organization,name='Retention project',steward=self.user)
        with tempfile.TemporaryDirectory() as temp, override_settings(PRIVATE_STORAGE_ROOT=Path(temp)):
            docs=[]
            for held in (False,True):
                doc=Document.objects.create(organization=self.user.organization,project=project,uploader=self.user,title='Synthetic file',status='deleted',legal_hold=held)
                key=write_private(b'Synthetic old file')
                version=DocumentVersion.objects.create(organization=self.user.organization,document=doc,version_no=1,storage_key=key,sha256='a'*64,mime='text/plain',file_type='TXT',byte_size=18,created_by=self.user)
                Document.objects.filter(pk=doc.pk).update(updated_at=timezone.now()-timedelta(days=40))
                docs.append((doc,version,key))
            call_command('enforce_retention',apply=True,stdout=io.StringIO())
            self.assertFalse((Path(temp)/docs[0][2]).exists())
            self.assertTrue((Path(temp)/docs[1][2]).exists())
            self.assertEqual(DocumentVersion.objects.count(),2)
            docs[0][0].refresh_from_db()
            self.assertIsNotNone(docs[0][0].purged_at)


class RuntimeRoleTests(TestCase):
    @skipUnless(connection.vendor=='postgresql','PostgreSQL-specific privileges')
    def test_runtime_role_has_no_schema_or_audit_mutation_privileges(self):
        with connection.cursor() as cursor:
            cursor.execute("CREATE ROLE secureai_app LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE")
        call_command('configure_runtime_role',stdout=io.StringIO())
        with connection.cursor() as cursor:
            cursor.execute("SELECT has_table_privilege('secureai_app','audit_auditevent','UPDATE'),has_table_privilege('secureai_app','audit_auditevent','DELETE'),has_table_privilege('secureai_app','audit_auditevent','INSERT'),has_schema_privilege('secureai_app','public','CREATE')")
            self.assertEqual(cursor.fetchone(),(False,False,True,False))
