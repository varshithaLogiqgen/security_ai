"""Environment-driven settings. Development uses synthetic accounts and SQLite."""
import os
from pathlib import Path
from urllib.parse import urlparse, unquote
from django.core.exceptions import ImproperlyConfigured
from django.core.management.utils import get_random_secret_key
from dotenv import load_dotenv
from .environment import value

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')
DEBUG = os.getenv('DJANGO_DEBUG', 'true').lower() == 'true'
SYNTHETIC_MODE = os.getenv('SYNTHETIC_MODE', 'true' if DEBUG else 'false').lower() == 'true'
if SYNTHETIC_MODE and not DEBUG:
    raise ImproperlyConfigured('Synthetic mode must not be enabled in production.')
VAR_DIR = Path(os.getenv('VAR_DIR', str(BASE_DIR / 'var')))
VAR_DIR.mkdir(parents=True, exist_ok=True)

def secret(name, factory):
    supplied = value(name)
    if supplied:
        return supplied
    if not DEBUG:
        raise ImproperlyConfigured(f'{name} is required in production.')
    path = VAR_DIR / name.lower()
    if not path.exists():
        try:
            with path.open('x', encoding='utf-8') as output:
                output.write(factory())
            path.chmod(0o600)
        except FileExistsError:
            pass
    return path.read_text(encoding='utf-8').strip()

SECRET_KEY = secret('DJANGO_SECRET_KEY', get_random_secret_key)
from cryptography.fernet import Fernet
DATA_ENCRYPTION_KEY = secret('DATA_ENCRYPTION_KEY', lambda: Fernet.generate_key().decode())
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,testserver').split(',')
CSRF_TRUSTED_ORIGINS = os.getenv('CSRF_TRUSTED_ORIGINS', 'http://127.0.0.1:5174,http://127.0.0.1:5173,http://127.0.0.1:4173,http://localhost:5174').split(',')
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://127.0.0.1:5174')
INSTALLED_APPS = [
    'django.contrib.auth', 'django.contrib.contenttypes', 'django.contrib.sessions',
    'django.contrib.messages', 'django.contrib.staticfiles', 'rest_framework',
    'apps.core', 'apps.identity', 'apps.projects', 'apps.work_updates', 'apps.people',
    'apps.documents', 'apps.assistant', 'apps.notifications', 'apps.administration', 'apps.audit',
]
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware', 'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'apps.core.middleware.SecurityHeadersMiddleware',
]
ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'
TEMPLATES = [{'BACKEND': 'django.template.backends.django.DjangoTemplates', 'DIRS': [BASE_DIR / 'templates'], 'APP_DIRS': True, 'OPTIONS': {'context_processors': ['django.template.context_processors.request', 'django.contrib.auth.context_processors.auth']}}]
database_url = value('DATABASE_URL')
if database_url:
    db = urlparse(database_url)
    if db.scheme not in {'postgres', 'postgresql'}:
        raise ImproperlyConfigured('DATABASE_URL must use PostgreSQL.')
    DATABASES = {'default': {'ENGINE': 'django.db.backends.postgresql', 'NAME': db.path.lstrip('/'), 'USER': unquote(db.username or ''), 'PASSWORD': unquote(db.password or ''), 'HOST': db.hostname, 'PORT': db.port or 5432, 'CONN_MAX_AGE': 60}}
    DATABASES['default']['OPTIONS'] = {'sslmode': os.getenv('DATABASE_SSLMODE', 'verify-full' if not DEBUG else 'prefer'), 'connect_timeout': 10}
    if os.getenv('DATABASE_SSLROOTCERT'):
        DATABASES['default']['OPTIONS']['sslrootcert'] = os.environ['DATABASE_SSLROOTCERT']
else:
    if not DEBUG:
        raise ImproperlyConfigured('PostgreSQL DATABASE_URL is required in production.')
    DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': VAR_DIR / 'db.sqlite3', 'OPTIONS': {'timeout': 20, 'transaction_mode': 'IMMEDIATE'}}}
AUTH_USER_MODEL = 'identity.User'
AUTH_PASSWORD_VALIDATORS = [{'NAME':'django.contrib.auth.password_validation.MinimumLengthValidator','OPTIONS':{'min_length':12}}, {'NAME':'django.contrib.auth.password_validation.CommonPasswordValidator'}]
LANGUAGE_CODE = 'en-us'
TIME_ZONE = os.getenv('TIME_ZONE', 'Asia/Kolkata')
USE_TZ = True
STATIC_URL = '/static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
APPEND_SLASH = False
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_AGE = int(os.getenv('SESSION_COOKIE_AGE', '3600'))
CSRF_COOKIE_SECURE = not DEBUG
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'no-referrer'
SECURE_SSL_REDIRECT = not DEBUG
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG
DATA_UPLOAD_MAX_MEMORY_SIZE = 11 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 1024 * 1024
PRIVATE_STORAGE_ROOT = VAR_DIR / 'private'
PRIVATE_STORAGE_ROOT.mkdir(parents=True, exist_ok=True)
MAX_FILE_SIZE = 10 * 1024 * 1024
LOCAL_AUTH_ENABLED = DEBUG and SYNTHETIC_MODE and os.getenv('LOCAL_AUTH_ENABLED', 'true').lower() == 'true'
OIDC_ISSUER = os.getenv('OIDC_ISSUER', '')
OIDC_CLIENT_ID = os.getenv('OIDC_CLIENT_ID', '')
OIDC_CLIENT_SECRET = value('OIDC_CLIENT_SECRET')
OIDC_MFA_AMR = os.getenv('OIDC_MFA_AMR', 'mfa,otp').split(',')
SCANNER_MODE = os.getenv('SCANNER_MODE', 'synthetic' if SYNTHETIC_MODE else 'clamav')
CLAMAV_HOST = os.getenv('CLAMAV_HOST', '127.0.0.1')
CLAMAV_PORT = int(os.getenv('CLAMAV_PORT', '3310'))
AI_ADAPTER = os.getenv('AI_ADAPTER', 'apps.assistant.providers.ExtractiveProvider')
OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://127.0.0.1:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.2')
AI_PROVIDER_APPROVED = os.getenv('AI_PROVIDER_APPROVED', 'false').lower() == 'true'
AI_APPROVAL_REFERENCE = os.getenv('AI_APPROVAL_REFERENCE', '')
OLLAMA_API_KEY = value('OLLAMA_API_KEY')
TRUST_PROXY_HEADERS = os.getenv('TRUST_PROXY_HEADERS', 'false').lower() == 'true'
if TRUST_PROXY_HEADERS:
    # Enable only behind the supplied isolated reverse proxy, never on a public API port.
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
RETENTION_POLICY_REFERENCE = os.getenv('RETENTION_POLICY_REFERENCE', '')
CHAT_RETENTION_DAYS = int(os.getenv('CHAT_RETENTION_DAYS', '0'))
DELETED_FILE_RETENTION_DAYS = int(os.getenv('DELETED_FILE_RETENTION_DAYS', '0'))
AUDIT_RETENTION_DAYS = int(os.getenv('AUDIT_RETENTION_DAYS', '0'))
BACKUP_RETENTION_DAYS = int(os.getenv('BACKUP_RETENTION_DAYS', '0'))
BACKUP_ENCRYPTION_KEY = value('BACKUP_ENCRYPTION_KEY')
BACKUP_ROOT = Path(os.getenv('BACKUP_ROOT', str(VAR_DIR / 'backups')))
CLAMAV_MAX_SIGNATURE_AGE_HOURS = int(os.getenv('CLAMAV_MAX_SIGNATURE_AGE_HOURS', '48'))
OIDC_HTTP_TIMEOUT = 10
if not DEBUG:
    from .production import validate_production
    validate_production(globals())
POLICY_ENABLED = True
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES':['apps.core.security.SessionAuthentication'],
    'DEFAULT_PERMISSION_CLASSES':['rest_framework.permissions.IsAuthenticated'],
    'DEFAULT_RENDERER_CLASSES':['rest_framework.renderers.JSONRenderer'],
    'EXCEPTION_HANDLER':'apps.core.api.exception_handler',
    'DEFAULT_THROTTLE_CLASSES':['apps.core.security.DatabaseThrottle'],
    'DEFAULT_THROTTLE_RATES':{'user':'120/min','search':'30/min','ai':'10/min'},
}

