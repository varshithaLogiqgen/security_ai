import time
from datetime import timedelta
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from rest_framework.authentication import SessionAuthentication as DRFSessionAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.throttling import BaseThrottle
from .models import RateBucket

class SessionAuthentication(DRFSessionAuthentication):
    def authenticate_header(self, request): return 'Session'
    def authenticate(self, request):
        result=super().authenticate(request)
        if not result: return None
        user,_=result
        if not user.organization.is_active: raise AuthenticationFailed('Your session has expired.')
        version=request.session.get('session_version')
        if version is not None and version!=user.session_version:
            request.session.flush()
            raise AuthenticationFailed('Your session has expired.')
        return result

class DatabaseThrottle(BaseThrottle):
    scope='user'
    limits={'user':120,'search':30,'ai':10}
    def allow_request(self,request,view):
        if not request.user.is_authenticated: return True
        key=f'{request.user.pk}:{self.scope}:{int(time.time())//60}'
        with transaction.atomic():
            bucket,_=RateBucket.objects.get_or_create(key=key,defaults={'expires_at':timezone.now()+timedelta(minutes=2)})
            RateBucket.objects.filter(pk=bucket.pk).update(count=F('count')+1)
            bucket.refresh_from_db()
        return bucket.count<=self.limits[self.scope]
    def wait(self): return 60

class SearchThrottle(DatabaseThrottle): scope='search'
class AIThrottle(DatabaseThrottle): scope='ai'
