from django.conf import settings
from django.core.management.base import BaseCommand,CommandError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction
from django.utils import timezone
from apps.identity.models import Organization,User,UserRole
from apps.projects.models import Team,TeamMembership,TeamLead,Project,ProjectMembership
from apps.work_updates.models import WorkUpdate
from apps.documents.models import Document,DocumentGrant
from apps.documents.services import stage
from apps.documents.processing import process_job

class Command(BaseCommand):
    help='Create synthetic pilot users and records. Safe to rerun; existing records are not reset.'
    def add_arguments(self,parser): parser.add_argument('--password',required=True)
    def handle(self,*args,**options):
        if not (settings.DEBUG and settings.SYNTHETIC_MODE): raise CommandError('Seeding requires local synthetic mode.')
        if len(options['password'])<12: raise CommandError('Use a password with at least 12 characters.')
        with transaction.atomic():
            org,_=Organization.objects.get_or_create(name='Northstar')
            users={}
            for username,name,title,team in [('asha','Asha Rao','Product engineer','Payments'),('ravi','Ravi Kumar','Software engineer','Payments'),('meera','Meera Iyer','Engineering lead','Payments'),('dev','Dev Shah','Platform engineer','Platform'),('admin','Organization Admin','Workspace administrator','Operations'),('reviewer','Independent Admin','Workspace administrator','Operations'),('security','Security Reviewer','Security administrator','Security'),('retention','Retention Steward','Records steward','Operations')]:
                user,created=User.objects.get_or_create(username=username,defaults={'organization':org,'name':name,'email':f'{username}@example.test','title':title,'directory_team':team})
                if created: user.set_password(options['password']);user.save()
                users[username]=user
            for username,role in [('admin','admin'),('reviewer','admin'),('security','audit'),('retention','retention')]:
                UserRole.objects.get_or_create(organization=org,user=users[username],role=role)
            team,_=Team.objects.get_or_create(organization=org,name='Payments')
            platform,_=Team.objects.get_or_create(organization=org,name='Platform')
            for name in ['asha','ravi']:
                TeamMembership.objects.get_or_create(organization=org,team=team,user=users[name])
            TeamMembership.objects.get_or_create(organization=org,team=platform,user=users['dev'])
            TeamLead.objects.get_or_create(organization=org,team=team,user=users['meera'])
            project,_=Project.objects.get_or_create(organization=org,name='Atlas',defaults={'code':'AT','description':'A reliable foundation for the next generation of payments.','steward':users['meera']})
            for name in ['asha','dev']:
                ProjectMembership.objects.get_or_create(organization=org,project=project,user=users[name])
            if not WorkUpdate.objects.filter(organization=org).exists():
                for status,visibility,body in [('published','lead_visible','Completed the Atlas payment retry flow. Integration testing is the next milestone.'),('draft','private','Exploring the reconciliation design. These synthetic notes are private.'),('published','private','Private planning notes for Atlas. Canary private-orchid-42.')]:
                    WorkUpdate.objects.create(organization=org,owner=users['asha'],team=team,work_date=timezone.localdate(),body=body,status=status,visibility=visibility)
            if not Document.objects.filter(project=project).exists():
                for title,classification,text in [('Atlas · Project overview','project','Atlas brings together the payment platform foundation. The next milestone is integration testing. Public canary atlas-bluebird-17.'),('Integration checklist','restricted','Atlas integration checklist: test retries, reconciliation and service boundaries. Restricted canary silver-maple-39.')]:
                    doc=Document.objects.create(organization=org,project=project,uploader=users['asha'],title=title,classification=classification)
                    version=stage(doc,SimpleUploadedFile('synthetic.txt',text.encode(),content_type='text/plain'),users['asha'])
                    process_job(version.processingjob.pk)
                    doc.refresh_from_db()
                    if doc.status!='unpublished': raise CommandError('Synthetic file processing failed.')
                    doc.status='published';doc.ever_published=True;doc.save()
                    if classification=='restricted': DocumentGrant.objects.create(organization=org,document=doc,grantee=users['asha'],assigned_by=users['asha'])
        self.stdout.write(self.style.SUCCESS('Synthetic workspace ready. Accounts: '+', '.join(users)+'. Passwords were set only for new accounts.'))
