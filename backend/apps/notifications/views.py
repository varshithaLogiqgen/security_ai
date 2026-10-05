from django.utils import timezone
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from apps.core.api import endpoint,page,object_or_404
from .models import Notification

@endpoint(['GET'])
def notifications(request):
    rows=Notification.objects.filter(organization=request.user.organization,user=request.user).order_by('-created_at','id')
    return Response(page(request,rows,lambda n:{'id':str(n.pk),'message':n.message,'date':n.created_at.isoformat()}))

@endpoint(['POST'])
def mark_read(request,pk):
    notification=object_or_404(Notification,pk,request.user)
    if notification.user_id!=request.user.pk: raise NotFound()
    notification.read_at=timezone.now();notification.save()
    return Response(status=204)
