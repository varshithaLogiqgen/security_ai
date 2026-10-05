import hashlib
import time
from datetime import timedelta
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db import transaction
from rest_framework.response import Response
from authlib.integrations.django_client import OAuth
from apps.core.api import endpoint
from apps.core.models import RateBucket
from apps.policy.service import active, role
from apps.projects.models import TeamMembership, TeamLead, Project
from apps.people.serializers import person
from apps.audit.service import record
from .models import User

def oauth_client():
    oauth = OAuth()
    oauth.register(name='organization', client_id=settings.OIDC_CLIENT_ID, client_secret=settings.OIDC_CLIENT_SECRET,
                   server_metadata_url=f'{settings.OIDC_ISSUER.rstrip("/")}/.well-known/openid-configuration',
                   client_kwargs={'scope':'openid email profile', 'code_challenge_method':'S256', 'timeout':settings.OIDC_HTTP_TIMEOUT})
    return oauth.create_client('organization')

def establish(request, user):
    login(request,user,backend='django.contrib.auth.backends.ModelBackend')
    request.session['session_version'] = user.session_version
    record(user,'session.started',user.pk)

@ensure_csrf_cookie
@csrf_protect
@require_http_methods(['GET','POST'])
def sign_in(request):
    if settings.OIDC_ISSUER and settings.OIDC_CLIENT_ID:
        if request.method != 'GET': return JsonResponse({'detail':'Use organization sign-in.'},status=405)
        return oauth_client().authorize_redirect(request,request.build_absolute_uri('/api/v1/auth/callback'))
    if not settings.LOCAL_AUTH_ENABLED:
        return JsonResponse({'detail':'Organization sign-in has not been configured.'},status=503)
    error = None
    if request.method == 'POST':
        # Login throttling is database-backed and does not reveal account existence.
        key = hashlib.sha256(f'login:{request.META.get("REMOTE_ADDR","")}:{int(time.time())//60}'.encode()).hexdigest()
        with transaction.atomic():
            bucket,_ = RateBucket.objects.select_for_update().get_or_create(key=key,defaults={'expires_at':timezone.now()+timedelta(minutes=2)})
            bucket.count += 1
            bucket.save()
        user = authenticate(request,username=request.POST.get('username','')[:150],password=request.POST.get('password','')) if bucket.count<=10 else None
        if user and user.is_active and user.organization.is_active:
            establish(request,user)
            return redirect(settings.FRONTEND_URL)
        error = 'Unable to sign in with those details. Please try again shortly.'
    return render(request,'identity/login.html',{'error':error})

@require_http_methods(['GET'])
def callback(request):
    if not settings.OIDC_ISSUER or not settings.OIDC_CLIENT_ID:
        return JsonResponse({'detail':'Sign-in is unavailable.'},status=503)
    try:
        # Authlib verifies state, nonce, ID-token signature, audience and expiry.
        token = oauth_client().authorize_access_token(request)
        claims = token['userinfo']
        if claims.get('iss') != settings.OIDC_ISSUER: raise ValueError()
        user = User.objects.filter(oidc_subject=claims['sub'],oidc_issuer=settings.OIDC_ISSUER,is_active=True,organization__is_active=True).first()
        # Never provision roles/orgs from an untrusted email or browser-supplied attributes.
        with transaction.atomic():
            if not user:
                from .invitations import redeem
                user = redeem(request, claims)
            if (role(user,'admin') or role(user,'audit')) and not set(claims.get('amr',[])).intersection(settings.OIDC_MFA_AMR): raise ValueError()
            establish(request,user)
    except Exception:
        return JsonResponse({'detail':'Unable to complete organization sign-in.'},status=401)
    return redirect(settings.FRONTEND_URL)

@require_http_methods(['GET'])
def accept_invitation(request):
    from .invitations import token_digest
    from apps.administration.models import Invitation
    digest = token_digest(request.GET.get('token', '')[:200])
    if not Invitation.objects.filter(token_hash=digest, accepted_at__isnull=True, expires_at__gt=timezone.now(), organization__is_active=True).exists():
        return JsonResponse({'detail':'Invitation unavailable.'}, status=404)
    if not settings.OIDC_ISSUER or not settings.OIDC_CLIENT_ID:
        return JsonResponse({'detail':'Organization sign-in must be configured to accept invitations.'}, status=503)
    request.session['invitation_hash'] = digest
    return redirect('/api/v1/auth/login')

@ensure_csrf_cookie
@endpoint(['GET'])
def me(request):
    user = request.user
    result = person(user)
    teams = active(TeamMembership.objects.filter(organization=user.organization,user=user,team__is_active=True)).select_related('team')
    led = active(TeamLead.objects.filter(organization=user.organization,user=user,team__is_active=True)).select_related('team')
    result.update(organization=user.organization.name,teams=[{'id':str(m.team_id),'name':m.team.name} for m in teams],led_teams=[{'id':str(m.team_id),'name':m.team.name} for m in led],capabilities=[r for r in ['admin','audit'] if role(user,r)]+(['lead'] if led.exists() else []))
    if any(role(user, r) for r in ['admin','audit','retention']) or Project.objects.filter(organization=user.organization, steward=user, is_active=True).exists():
        result['capabilities'].append('approvals')
    return Response(result)

@endpoint(['POST'])
def sign_out(request):
    record(request.user,'session.ended',request.user.pk)
    logout(request)
    return Response(status=204)

@ensure_csrf_cookie
@require_http_methods(['GET'])
def csrf(request):
    return JsonResponse({'detail':'CSRF cookie initialized.'})
