from django.conf import settings
from django.db import transaction
from django.utils.module_loading import import_string
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from apps.core.api import endpoint,object_or_404,require,validated,page,AIThrottle,Unavailable
from apps.identity.models import Organization
from apps.policy.service import POLICY_VERSION
from apps.audit.service import record
from apps.search.service import retrieve,resolve_source,source_title
from .models import Conversation,Message,AnswerSource
from .serializers import QuestionInput,conversation_data

INSUFFICIENT='I couldn’t find enough information in your accessible sources to answer that question.'

@endpoint(['GET','POST'])
def conversations(request):
    if request.method=='POST':
        obj=Conversation.objects.create(organization=request.user.organization,owner=request.user)
        record(request.user,'conversation.created',obj.pk)
        return Response(conversation_data(obj,request.user),status=201)
    rows=Conversation.objects.filter(organization=request.user.organization,owner=request.user,is_deleted=False).order_by('-created_at','id')
    return Response(page(request,rows,lambda c:conversation_data(c,request.user,False)))

@endpoint(['GET','DELETE'])
def conversation(request,pk):
    obj=object_or_404(Conversation,pk,request.user)
    require(request.user,'conversation.read',obj)
    if request.method=='DELETE':
        obj.is_deleted=True;obj.save()
        record(request.user,'conversation.deleted',obj.pk)
        return Response(status=204)
    return Response(conversation_data(obj,request.user))

@endpoint(['POST','GET'],lock=False,throttle=AIThrottle)
def messages(request,pk):
    with transaction.atomic():
        Organization.objects.select_for_update().get(pk=request.user.organization_id)
        obj=object_or_404(Conversation,pk,request.user)
        require(request.user,'conversation.read',obj)
        if request.method=='GET': return Response(conversation_data(obj,request.user))
        data=validated(QuestionInput,request)
        evidence=[e for e in retrieve(request.user,data['question'],limit=6) if resolve_source(request.user,e)]
        # At most 6 bounded, freshly authorized excerpts leave this transaction.
        for e in evidence: e.excerpt=e.excerpt[:2500]
    answer=INSUFFICIENT
    indexes=[]
    if evidence:
        result=import_string(settings.AI_ADAPTER)().answer(data['question'],evidence)
        if not isinstance(result,dict) or not isinstance(result.get('answer'),str) or not isinstance(result.get('citations'),list): raise Unavailable('The answer could not be validated.')
        indexes=result['citations']
        if any(type(i) is not int or i<0 or i>=len(evidence) for i in indexes) or len(result['answer'])>16000: raise Unavailable('The answer could not be validated.')
        indexes=list(dict.fromkeys(indexes))
        if indexes and result['answer'].strip(): answer=result['answer']
        else: indexes=[]
    with transaction.atomic():
        Organization.objects.select_for_update().get(pk=request.user.organization_id)
        obj=object_or_404(Conversation,pk,request.user)
        require(request.user,'conversation.read',obj)
        # Revalidate every excerpt, including uncited context that could influence the answer.
        changed=any(not resolve_source(request.user,e) for e in evidence)
        message=Message.objects.create(organization=request.user.organization,conversation=obj,question=data['question'],answer='' if changed else answer,state='access_changed' if changed else 'answered' if indexes else 'insufficient',policy_version=POLICY_VERSION)
        if not changed:
            for index, source in enumerate(evidence):
                AnswerSource.objects.create(organization=request.user.organization,message=message,source_type=source.source_type,source_id=source.source_id,version=source.version,locator=source.locator,is_citation=index in indexes)
        obj.title=data['question'][:60];obj.save()
        record(request.user,'assistant.answered',message.pk,'deny' if changed else 'allow','sources_changed' if changed else 'validated_sources')
        return Response(conversation_data(obj,request.user),status=201)

@endpoint(['GET'])
def citation(request,pk):
    source=object_or_404(AnswerSource,pk,request.user)
    if not source.is_citation: raise NotFound()
    require(request.user,'conversation.read',source.message.conversation)
    resource=resolve_source(request.user,source)
    if not resource: raise NotFound()
    return Response({'id':str(source.pk),'title':source_title(source,resource),'source_type':source.source_type,'source_id':str(source.source_id),'version':source.version,'locator':source.locator})
