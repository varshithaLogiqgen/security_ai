import subprocess
import sys
import time
from datetime import timedelta
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from apps.documents.models import ProcessingJob,Document

class Command(BaseCommand):
    help='Run the database-backed upload queue. Each parser runs in a time-bounded subprocess.'
    def add_arguments(self,parser): parser.add_argument('--once',action='store_true')
    def handle(self,*args,**options):
        while True:
            with transaction.atomic():
                # A crashed worker never leaves a publishable document behind.
                expired=ProcessingJob.objects.filter(status='running',started_at__lt=timezone.now()-timedelta(minutes=5))
                for stale in expired:
                    Document.objects.filter(current_version=stale.version,status='processing').update(status='failed')
                expired.update(status='failed',error_code='worker_expired',completed_at=timezone.now())
                job=ProcessingJob.objects.select_for_update().filter(status='pending').order_by('created_at').first()
                if job:
                    job.status='running';job.started_at=timezone.now();job.save()
            if not job:
                if options['once']: break
                time.sleep(2)
                continue
            try:
                completed=subprocess.run([sys.executable,str(settings.BASE_DIR/'manage.py'),'process_document',str(job.pk)],timeout=60,capture_output=True)
                if completed.returncode: raise RuntimeError()
            except (subprocess.TimeoutExpired,RuntimeError):
                ProcessingJob.objects.filter(pk=job.pk).update(status='failed',error_code='worker_failed',completed_at=timezone.now())
                Document.objects.filter(current_version=job.version,status='processing').update(status='failed')
            self.stdout.write(f'Processed job {job.pk}')
