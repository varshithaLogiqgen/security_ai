from django.core.management.base import BaseCommand
from apps.documents.processing import process_job

class Command(BaseCommand):
    help='Process one private file in a dedicated worker process.'
    def add_arguments(self,parser): parser.add_argument('job_id')
    def handle(self,*args,**options): process_job(options['job_id'])
