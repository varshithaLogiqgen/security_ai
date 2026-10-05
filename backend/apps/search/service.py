"""Retrieval returns authorized evidence only. P2 has no path into this module."""
import re
from dataclasses import dataclass
from django.db import connection
from django.db.models import Q, F
from apps.identity.models import User
from apps.documents.models import Document, DocumentChunk
from apps.work_updates.models import WorkUpdate
from apps.policy.service import authorize, visible_documents, visible_updates

STOP_WORDS = {'a','an','the','is','are','what','who','how','my','me','tell','about','of','on','in','and','for','to','with','please','summarize'}

@dataclass
class Evidence:
    source_type: str
    source_id: str
    version: int
    title: str
    excerpt: str
    locator: str

def matching(qs, fields, query):
    terms=[t for t in re.findall(r'[\w-]+',query.lower()) if t not in STOP_WORDS][:20]
    if not terms: return qs.none()
    if connection.vendor=='postgresql':
        from django.contrib.postgres.search import SearchVector, SearchQuery
        search=None
        for term in terms:
            search=SearchQuery(term,config='english') if search is None else search | SearchQuery(term,config='english')
        return qs.annotate(search_document=SearchVector(*fields,config='english')).filter(search_document=search)
    condition=Q()
    for term in terms:
        for field in fields: condition |= Q(**{f'{field}__icontains':term})
    return qs.filter(condition)

def retrieve(user,query,limit=250):
    evidence=[]
    documents=visible_documents(user,published_only=True)
    chunks=DocumentChunk.objects.filter(organization=user.organization,version__document__in=documents,version_id=F('version__document__current_version_id'))
    chunk_ids=matching(chunks,['text'],query).values_list('version__document_id',flat=True)
    title_ids=matching(documents,['title'],query).values_list('id',flat=True)
    for doc in documents.filter(Q(pk__in=chunk_ids)|Q(pk__in=title_ids)).order_by('-updated_at','id')[:limit]:
        if not authorize(user,'document.retrieve',doc).allow: continue
        excerpt_chunks=matching(doc.current_version.chunks.all(),['text'],query)[:2]
        if not excerpt_chunks.exists(): excerpt_chunks=doc.current_version.chunks.order_by('ordinal')[:1]
        text='\n'.join(c.text for c in excerpt_chunks)[:3500]
        if text: evidence.append(Evidence('document',str(doc.pk),doc.version,doc.title,text,'Current document'))
    for update in matching(visible_updates(user),['body','team__name'],query).order_by('-work_date','id')[:limit]:
        if authorize(user,'update.read',update).allow:
            evidence.append(Evidence('update',str(update.pk),update.version,f'{update.team.name} · {update.work_date}',update.body[:3500],'Work update'))
    for profile in matching(User.objects.filter(organization=user.organization,is_active=True),['name','email','title','directory_team'],query).order_by('name','id')[:limit]:
        if authorize(user,'profile.read',profile).allow:
            evidence.append(Evidence('profile',str(profile.pk),profile.profile_version,profile.name,f'{profile.name} · {profile.title} · {profile.directory_team} · {profile.email}','Work directory'))
    return evidence[:limit]

def resolve_source(user,source):
    model,action={'document':(Document,'document.retrieve'),'update':(WorkUpdate,'update.read'),'profile':(User,'profile.read')}.get(source.source_type,(None,None))
    if not model: return None
    resource=model.objects.filter(pk=source.source_id,organization=user.organization).first()
    if not resource or not authorize(user,action,resource).allow: return None
    version=resource.profile_version if source.source_type=='profile' else resource.version
    return resource if version==source.version else None

def source_title(source,resource):
    if source.source_type=='document': return resource.title
    if source.source_type=='profile': return resource.name
    return f'{resource.team.name} · {resource.work_date}'
