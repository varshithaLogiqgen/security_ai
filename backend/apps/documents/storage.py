"""Encrypted private files; storage keys are never serialized or served as URLs."""
import uuid
from cryptography.fernet import Fernet
from django.conf import settings

def write_private(data):
    key = f'{uuid.uuid4().hex}.enc'
    path = settings.PRIVATE_STORAGE_ROOT / key
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(Fernet(settings.DATA_ENCRYPTION_KEY.encode()).encrypt(data))
    path.chmod(0o600)
    return key

def read_private(key):
    if len(key)!=36 or not key.endswith('.enc'):
        raise ValueError('Invalid storage key.')
    uuid.UUID(hex=key[:-4])
    return Fernet(settings.DATA_ENCRYPTION_KEY.encode()).decrypt((settings.PRIVATE_STORAGE_ROOT/key).read_bytes())
