import io
import re
import socket
import struct
import zipfile
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from defusedxml import ElementTree
from pypdf import PdfReader
from apps.identity.models import Organization
from apps.audit.service import record
from .models import ProcessingJob, DocumentChunk, Document
from .storage import read_private

class ProcessingError(Exception): pass

def scan(data):
    if settings.SCANNER_MODE == 'synthetic':
        if not (settings.DEBUG and settings.SYNTHETIC_MODE): raise ProcessingError('scanner_unavailable')
        if b'EICAR-STANDARD-ANTIVIRUS-TEST-FILE' in data: raise ProcessingError('malware_detected')
        return
    if settings.SCANNER_MODE != 'clamav': raise ProcessingError('scanner_unavailable')
    try:
        with socket.create_connection((settings.CLAMAV_HOST,settings.CLAMAV_PORT),timeout=15) as client:
            client.sendall(b'zINSTREAM\0')
            for offset in range(0,len(data),65536):
                chunk=data[offset:offset+65536]
                client.sendall(struct.pack('!I',len(chunk))+chunk)
            client.sendall(struct.pack('!I',0))
            reply=b''
            while b'\0' not in reply and len(reply)<4096:
                part=client.recv(4096)
                if not part: break
                reply+=part
        if b'FOUND' in reply: raise ProcessingError('malware_detected')
        if reply.rstrip(b'\0\n') != b'stream: OK': raise ProcessingError('scanner_unavailable')
    except (OSError,TimeoutError): raise ProcessingError('scanner_unavailable')

def extract(data,file_type):
    if file_type == 'TXT':
        if b'\0' in data: raise ProcessingError('invalid_file')
        return data.decode('utf-8-sig')
    if file_type == 'PDF':
        if not data.startswith(b'%PDF-'): raise ProcessingError('invalid_file')
        pdf=PdfReader(io.BytesIO(data),strict=True)
        if pdf.is_encrypted or len(pdf.pages)>500: raise ProcessingError('invalid_file')
        return '\n'.join(page.extract_text() or '' for page in pdf.pages)
    if file_type == 'DOCX':
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            entries=archive.infolist()
            if len(entries)>1000 or sum(e.file_size for e in entries)>30*1024*1024: raise ProcessingError('invalid_file')
            if any('vbaproject' in e.filename.lower() for e in entries): raise ProcessingError('invalid_file')
            xml=archive.read('word/document.xml')
        root=ElementTree.fromstring(xml)
        return '\n'.join(node.text or '' for node in root.iter() if node.tag.endswith('}t'))
    raise ProcessingError('invalid_file')

def process_job(job_id):
    job=ProcessingJob.objects.select_related('version__document','version__created_by').get(pk=job_id)
    if job.status not in {'pending','running'}: return
    version=job.version
    text=''
    error=''
    try:
        data=read_private(version.storage_key)
        scan(data)
        text=extract(data,version.file_type)
        if not text.strip() or len(text)>2_000_000: raise ProcessingError('unsupported_content')
        if re.search(r'\b(payroll|salary|national\s+id|medical\s+record|performance\s+review|hr\s+case)\b',text,re.I): raise ProcessingError('excluded_data')
    except ProcessingError as exc: error=str(exc)
    except Exception: error='extraction_failed'
    with transaction.atomic():
        Organization.objects.select_for_update().get(pk=job.organization_id)
        job=ProcessingJob.objects.select_for_update().get(pk=job_id)
        document=Document.objects.select_for_update().get(pk=version.document_id)
        if job.status not in {'pending','running'}: return
        job.error_code=error
        job.status='failed' if error else 'completed'
        job.completed_at=timezone.now()
        job.save()
        if not error:
            words=text.split()
            for index,start in enumerate(range(0,len(words),600)):
                DocumentChunk.objects.create(organization=job.organization,version=version,ordinal=index,text=' '.join(words[start:start+720]),locator=f'Section {index+1}')
        if document.current_version_id==version.pk and document.status!='deleted':
            document.status='quarantined' if error in {'malware_detected','excluded_data'} else 'failed' if error else 'unpublished'
            document.save()
        record(version.created_by,'document.processed',document.pk,'deny' if error else 'allow',error or 'processed')
