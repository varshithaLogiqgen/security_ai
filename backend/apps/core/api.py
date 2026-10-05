import hashlib
import json
import time
import uuid
from functools import wraps
from datetime import timedelta
from django.core import signing
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction, IntegrityError, DatabaseError
from django.db.models import F
from django.utils import timezone
from rest_framework import authentication, serializers
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.exceptions import APIException, NotFound, AuthenticationFailed, ValidationError
from rest_framework.response import Response
from rest_framework.throttling import BaseThrottle
from rest_framework.views import exception_handler as drf_exception_handler
from apps.identity.models import Organization
from apps.policy.service import live, authorize
from apps.audit.service import record
from .models import IdempotencyRecord, RateBucket

class Conflict(APIException):
    status_code = 409
    default_detail = 'This item changed or this request was already submitted. Reload before retrying.'

class Unavailable(APIException):
    status_code = 503
    default_detail = 'This service is temporarily unavailable.'

from .security import SessionAuthentication, DatabaseThrottle, SearchThrottle, AIThrottle

def exception_handler(exc, context):
    request = context.get('request')
    if isinstance(exc, (NotFound,)):
        if request and request.user.is_authenticated:
            record(request.user, 'access.denied', '', 'deny', 'not_found_or_denied')
        return Response({'detail':'This page is unavailable or you no longer have access.'},status=404)
    if isinstance(exc, (DjangoValidationError, IntegrityError)):
        return Response({'detail':'The supplied values or relationships are not valid.'},status=400)
    if isinstance(exc, DatabaseError):
        return Response({'detail':'This service is temporarily unavailable.'},status=503)
    response = drf_exception_handler(exc,context)
    if response is None:
        return Response({'detail':'We couldn’t complete that request.'},status=500)
    return response

def object_or_404(model, value, user, lock=False):
    try: pk = uuid.UUID(str(value))
    except (ValueError, TypeError, AttributeError): raise NotFound()
    qs = model.objects.filter(pk=pk,organization=user.organization)
    if lock: qs = qs.select_for_update()
    result = qs.first()
    if not result: raise NotFound()
    return result

def require(user, action, resource=None):
    try: decision = authorize(user,action,resource)
    except DatabaseError: raise Unavailable()
    if not decision.allow: raise NotFound()
    return decision

def version_check(request, obj):
    value = request.headers.get('If-Match', request.data.get('version'))
    try: value = int(str(value).strip('"'))
    except (ValueError, TypeError): raise Conflict()
    if obj.version != value: raise Conflict()

def validated(serializer, request):
    data = request.data
    unknown = set(data) - set(serializer().fields)
    if unknown: raise ValidationError('Unsupported request fields.')
    instance = serializer(data=data)
    instance.is_valid(raise_exception=True)
    return instance.validated_data

def page(request, rows, serialize=lambda row:row, query=None):
    query = query if query is not None else request.query_params
    cursor = query.get('cursor')
    scope = hashlib.sha256(json.dumps({k:str(v) for k,v in query.items() if k!='cursor'},sort_keys=True).encode()).hexdigest()
    offset = 0
    if cursor:
        try:
            payload = signing.loads(cursor,salt='pagination',max_age=3600)
            if payload['user'] != str(request.user.pk) or payload['scope'] != scope or payload['path'] != request.path: raise ValueError()
            offset = int(payload['offset'])
            if offset < 0: raise ValueError()
        except (signing.BadSignature, ValueError, KeyError, TypeError): raise ValidationError('Invalid cursor.')
    rows = list(rows)
    size = 25
    selected = rows[offset:offset+size]
    next_cursor = signing.dumps({'user':str(request.user.pk),'scope':scope,'path':request.path,'offset':offset+size},salt='pagination') if len(rows)>offset+size else None
    return {'results':[serialize(row) for row in selected], 'next':next_cursor}

def endpoint(methods, *, lock=True, throttle=None):
    def decorate(function):
        @wraps(function)
        def wrapped(request, *args, **kwargs):
            user = live(request.user)
            if not user: raise NotFound()
            request.user = user
            if not lock:
                return function(request,*args,**kwargs)
            with transaction.atomic():
                Organization.objects.select_for_update().get(pk=user.organization_id)
                current = live(user)
                if not current: raise NotFound()
                request.user = current
                idem = None
                if request.method in {'POST','PATCH','DELETE'} and not request.path.endswith('/search'):
                    key = request.headers.get('Idempotency-Key')
                    if key:
                        if len(key)>100: raise ValidationError('Invalid idempotency key.')
                        fingerprint = hashlib.sha256(f'{request.method}:{request.path}'.encode()).hexdigest()
                        if IdempotencyRecord.objects.filter(user=user,key=key).exists(): raise Conflict()
                        idem = IdempotencyRecord.objects.create(organization=user.organization,user=user,key=key,fingerprint=fingerprint)
                response = function(request,*args,**kwargs)
                if idem:
                    idem.status = response.status_code
                    idem.save(update_fields=['status'])
                return response
        if throttle:
            wrapped = throttle_classes([throttle])(wrapped)
        return api_view(methods)(wrapped)
    return decorate

class VersionInput(serializers.Serializer):
    version = serializers.IntegerField(min_value=1,required=False)
