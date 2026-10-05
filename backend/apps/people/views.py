import json
from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.db.models import Q
from rest_framework.response import Response
from apps.identity.models import User
from apps.core.api import endpoint, require, object_or_404, validated, page, Unavailable
from apps.audit.service import record
from .models import PersonalProfile
from .serializers import person, WorkProfileInput, PersonalInput

@endpoint(['GET'])
def directory(request):
    q = request.query_params.get('q','')[:300]
    rows = User.objects.filter(organization=request.user.organization,is_active=True).filter(Q(name__icontains=q)|Q(email__icontains=q)|Q(title__icontains=q)|Q(directory_team__icontains=q)).order_by('name','id')
    return Response(page(request,rows,person))

@endpoint(['GET','PATCH'])
def profile(request, pk):
    user = object_or_404(User,pk,request.user)
    require(request.user,'profile.edit' if request.method=='PATCH' else 'profile.read',user)
    if request.method == 'PATCH':
        user.bio = validated(WorkProfileInput,request)['bio']
        user.profile_version += 1
        user.save(update_fields=['bio','profile_version'])
        record(request.user,'profile.updated',user.pk)
    return Response(person(user))

@endpoint(['GET','PATCH'])
def personal(request,pk):
    user = object_or_404(User,pk,request.user)
    require(request.user,'personal.edit' if request.method=='PATCH' else 'personal.read',user)
    cipher = Fernet(settings.DATA_ENCRYPTION_KEY.encode())
    if request.method == 'PATCH':
        data = validated(PersonalInput,request)
        PersonalProfile.objects.update_or_create(organization=user.organization,user=user,defaults={'encrypted_data':cipher.encrypt(json.dumps(data).encode()).decode()})
        record(user,'personal.updated',user.pk)
    obj = PersonalProfile.objects.filter(user=user,organization=user.organization).first()
    try: data = json.loads(cipher.decrypt(obj.encrypted_data.encode())) if obj else {'phone':'','address':'','emergency_contact':''}
    except (InvalidToken,ValueError): raise Unavailable()
    return Response(data)
