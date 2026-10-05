import json
import uuid
from datetime import timedelta
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from django.contrib.sessions.models import Session
from apps.identity.models import Organization
from apps.assistant.models import Conversation
from apps.documents.models import Document, DocumentChunk
from apps.audit.models import AuditEvent
from apps.audit.service import record
from apps.core.models import RateBucket


class Command(BaseCommand):
    help = 'Report retention candidates; --apply removes expired chats and approved tombstoned file contents, respecting legal holds.'

    def add_arguments(self, parser): parser.add_argument('--apply', action='store_true')

    def handle(self, *args, **options):
        if not settings.RETENTION_POLICY_REFERENCE or min(settings.CHAT_RETENTION_DAYS, settings.DELETED_FILE_RETENTION_DAYS, settings.AUDIT_RETENTION_DAYS) <= 0:
            raise CommandError('Configure approved retention periods and RETENTION_POLICY_REFERENCE first.')
        now = timezone.now()
        counts = {'chats':0, 'files':0, 'audit_archive_due':0, 'applied':options['apply']}
        for org_id in Organization.objects.values_list('pk', flat=True):
            with transaction.atomic():
                Organization.objects.select_for_update().get(pk=org_id)
                # Expire a chat only after its newest message and creation are old enough.
                from django.db.models import Max
                chats = Conversation.objects.filter(organization_id=org_id,legal_hold=False,created_at__lt=now-timedelta(days=settings.CHAT_RETENTION_DAYS)).annotate(last_message=Max('messages__created_at'))
                for chat in chats:
                    if chat.last_message and chat.last_message >= now-timedelta(days=settings.CHAT_RETENTION_DAYS): continue
                    counts['chats'] += 1
                    if options['apply']:
                        record(chat.owner,'retention.chat.purged',chat.pk,reason='approved_retention')
                        chat.delete()
                docs = Document.objects.filter(organization_id=org_id,status='deleted',legal_hold=False,purged_at__isnull=True,updated_at__lt=now-timedelta(days=settings.DELETED_FILE_RETENTION_DAYS))
                for doc in docs:
                    counts['files'] += 1
                    if options['apply']:
                        # Preserve immutable version metadata; erase only approved content.
                        for version in doc.versions.all():
                            key = version.storage_key
                            if len(key)!=36 or not key.endswith('.enc'): raise CommandError('Invalid storage key; purge stopped.')
                            uuid.UUID(hex=key[:-4])
                            (settings.PRIVATE_STORAGE_ROOT/key).unlink(missing_ok=True)
                        DocumentChunk.objects.filter(version__document=doc).delete()
                        doc.purged_at=now
                        doc.save(update_fields=['purged_at'])
                        record(doc.uploader,'retention.file.purged',doc.pk,reason='approved_retention')
                counts['audit_archive_due'] += AuditEvent.objects.filter(organization_id=org_id,created_at__lt=now-timedelta(days=settings.AUDIT_RETENTION_DAYS)).count()
        if options['apply']:
            Session.objects.filter(expire_date__lt=now).delete()
            RateBucket.objects.filter(expires_at__lt=now).delete()
        self.stdout.write(json.dumps(counts))
        if counts['audit_archive_due']:
            self.stderr.write('Audit records require reviewed immutable archival; this command never deletes audit history.')
