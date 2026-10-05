import json
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from apps.identity.models import Organization, User, UserRole
from apps.projects.models import Team, TeamLead
from apps.work_updates.models import WorkUpdate
from apps.audit.service import record


class DashboardTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.org=Organization.objects.create(name='Dashboard org')
        cls.other=Organization.objects.create(name='Other org')
        for name in ['employee','lead','admin','security']:
            setattr(cls,name,User.objects.create_user(username=name,organization=cls.org,name=name,email=f'{name}@example.test'))
        cls.outside=User.objects.create_user(username='outside',organization=cls.other,name='OUTSIDE_CANARY',email='outside@example.test')
        cls.team=Team.objects.create(organization=cls.org,name='Development')
        cls.assignment=TeamLead.objects.create(organization=cls.org,team=cls.team,user=cls.lead)
        UserRole.objects.create(organization=cls.org,user=cls.admin,role='admin')
        UserRole.objects.create(organization=cls.org,user=cls.security,role='audit')
        cls.shared=WorkUpdate.objects.create(organization=cls.org,owner=cls.employee,team=cls.team,work_date=timezone.localdate(),body='Visible blocker',is_blocked=True,status='published',visibility='lead_visible')
        WorkUpdate.objects.create(organization=cls.org,owner=cls.employee,team=cls.team,work_date=timezone.localdate(),body='PRIVATE_CANARY',is_blocked=True,status='published',visibility='private')
        WorkUpdate.objects.create(organization=cls.org,owner=cls.employee,team=cls.team,work_date=timezone.localdate(),body='DRAFT_CANARY',is_blocked=True)

    def read(self,user,query=''):
        client=APIClient();client.force_authenticate(user)
        return client.get('/api/v1/dashboard'+query)

    def test_employee_counts_are_exact_and_role_views_are_denied(self):
        for index in range(26):
            WorkUpdate.objects.create(organization=self.org,owner=self.employee,team=self.team,work_date=timezone.localdate(),body=f'Synthetic draft {index}')
        result=self.read(self.employee).json()
        self.assertEqual(result['cards']['drafts'],27)
        self.assertEqual(result['cards']['published'],2)
        self.assertEqual(len(result['updates']),5)
        self.assertEqual(result['available_views'],['employee'])
        for view in ['admin','security','lead']:
            self.assertEqual(self.read(self.employee,f'?view={view}').status_code,404)

    def test_lead_blockers_exclude_private_and_drafts_and_follow_date(self):
        result=self.read(self.lead).json()
        self.assertEqual(result['view'],'lead')
        self.assertEqual(result['cards']['blockers'],1)
        self.assertEqual(result['cards']['updates_today'],1)
        self.assertNotIn('PRIVATE_CANARY',json.dumps(result))
        self.assertNotIn('DRAFT_CANARY',json.dumps(result))
        prior=(timezone.localdate()-timedelta(days=1)).isoformat()
        self.assertEqual(self.read(self.lead,f'?date={prior}').json()['cards']['blockers'],0)
        TeamLead.objects.filter(pk=self.assignment.pk).update(revoked_at=timezone.now())
        self.assertEqual(self.read(self.lead,'?view=lead').status_code,404)
        self.assertEqual(self.read(self.lead).json()['view'],'employee')

    def test_admin_only_sees_org_metadata_and_own_administrative_events(self):
        record(self.admin,'admin.team_membership.applied',self.team.pk)
        record(self.security,'admin.secret.applied','OTHER_ACTOR_CANARY')
        result=self.read(self.admin).json()
        self.assertEqual(result['view'],'admin')
        self.assertEqual(result['cards']['accounts'],4)
        text=json.dumps(result)
        for canary in ['PRIVATE_CANARY','DRAFT_CANARY','OUTSIDE_CANARY','OTHER_ACTOR_CANARY']:
            self.assertNotIn(canary,text)
        self.assertEqual(self.read(self.admin,'?view=security').status_code,404)

    def test_security_filters_are_metadata_only_and_tenant_scoped(self):
        record(self.employee,'access.denied','none','deny','not_found_or_denied')
        record(self.admin,'admin.team_membership.applied',self.team.pk)
        record(self.outside,'access.denied','OUTSIDE_CANARY','deny')
        result=self.read(self.security,'?event=permissions').json()
        self.assertEqual(result['cards']['denials'],1)
        self.assertEqual(result['cards']['permissions'],1)
        self.assertEqual(len(result['events']),1)
        self.assertNotIn('PRIVATE_CANARY',json.dumps(result))
        self.assertNotIn('OUTSIDE_CANARY',json.dumps(result))
        self.assertNotIn('DATA_ENCRYPTION_KEY',json.dumps(result))

    def test_invalid_filters_and_expired_privilege(self):
        self.assertEqual(self.read(self.lead,'?date=invalid').status_code,400)
        self.assertEqual(self.read(self.security,'?event=unknown').status_code,400)
        UserRole.objects.filter(user=self.admin).update(revoked_at=timezone.now())
        self.assertEqual(self.read(self.admin,'?view=admin').status_code,404)

    def test_lead_can_create_own_update_only_for_a_currently_led_team(self):
        client=APIClient();client.force_authenticate(self.lead)
        payload={'team_id':str(self.team.pk),'work_date':timezone.localdate().isoformat(),'body':'My own lead progress update','is_blocked':True}
        response=client.post('/api/v1/updates',payload,format='json')
        self.assertEqual(response.status_code,201)
        self.assertEqual(response.json()['owner_id'],str(self.lead.pk))
        self.assertEqual(response.json()['visibility'],'private')
        self.assertTrue(response.json()['is_blocked'])
        TeamLead.objects.filter(pk=self.assignment.pk).update(revoked_at=timezone.now())
        self.assertEqual(client.post('/api/v1/updates',payload,format='json').status_code,404)
