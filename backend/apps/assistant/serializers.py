from rest_framework import serializers
from apps.search.service import resolve_source,source_title

class QuestionInput(serializers.Serializer):
    question=serializers.CharField(min_length=2,max_length=4000)

def message_data(message,user):
    citations=[]
    for source in message.sources.all():
        resource=resolve_source(user,source)
        if not resource:
            return {'id':str(message.pk),'question':message.question,'state':'access_changed','citations':[]}
        if source.is_citation:
            citations.append({'id':str(source.pk),'title':source_title(source,resource),'source_type':source.source_type,'source_id':str(source.source_id),'version':source.version,'locator':source.locator})
    result={'id':str(message.pk),'question':message.question,'state':message.state,'citations':citations}
    if message.state!='access_changed': result['answer']=message.answer
    return result

def conversation_data(conversation,user,include_messages=True):
    return {'id':str(conversation.pk),'title':conversation.title,'messages':[message_data(m,user) for m in conversation.messages.order_by('created_at','id')] if include_messages else []}
