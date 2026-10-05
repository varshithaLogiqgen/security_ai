from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from apps.core.api import endpoint,page
from apps.policy.service import role
from .models import AuditEvent

@endpoint(['GET'])
def events(request):
    rows=AuditEvent.objects.filter(organization=request.user.organization)
    if not role(request.user,'audit'):
        if not role(request.user,'admin'): raise NotFound()
        rows=rows.filter(actor=request.user,action__startswith='admin.',decision='allow')
    term=request.query_params.get('q','')[:100]
    rows=rows.filter(action__icontains=term).order_by('-created_at','id')
    return Response(page(request,rows,lambda a:{'id':str(a.pk),'actor':str(a.actor_id or ''),'action':a.action,'target':a.target,'decision':a.decision,'reason':a.reason,'policy_version':a.policy_version,'date':a.created_at.isoformat()}))
