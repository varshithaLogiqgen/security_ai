from rest_framework import serializers
from rest_framework.response import Response
from apps.core.api import endpoint,validated,page,SearchThrottle
from .service import retrieve,resolve_source

class SearchInput(serializers.Serializer):
    query=serializers.CharField(max_length=300)
    cursor=serializers.CharField(required=False,allow_blank=True,allow_null=True,max_length=2000)

@endpoint(['POST'],throttle=SearchThrottle)
def search(request):
    data=validated(SearchInput,request)
    evidence=[e for e in retrieve(request.user,data['query']) if resolve_source(request.user,e)]
    return Response(page(request,evidence,lambda e:{'id':e.source_id,'title':e.title,'snippet':e.excerpt[:300],'type':e.source_type},query=data))
