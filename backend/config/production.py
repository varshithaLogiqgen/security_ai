from urllib.parse import urlparse
from cryptography.fernet import Fernet
from django.core.exceptions import ImproperlyConfigured


def validate_production(config):
    errors = []
    for key in ('OIDC_ISSUER', 'FRONTEND_URL'):
        url = urlparse(config.get(key, ''))
        if url.scheme != 'https' or not url.hostname or url.username or url.query or url.fragment:
            errors.append(f'{key} must be an HTTPS URL without credentials, query or fragment')
    for key in ('OIDC_CLIENT_ID', 'OIDC_CLIENT_SECRET', 'AI_APPROVAL_REFERENCE', 'RETENTION_POLICY_REFERENCE'):
        if not config.get(key): errors.append(f'{key} is required')
    for key in ('CHAT_RETENTION_DAYS', 'DELETED_FILE_RETENTION_DAYS', 'AUDIT_RETENTION_DAYS', 'BACKUP_RETENTION_DAYS'):
        if config.get(key, 0) <= 0: errors.append(f'{key} must be an approved positive number')
    for key in ('DATA_ENCRYPTION_KEY', 'BACKUP_ENCRYPTION_KEY'):
        try: Fernet(config.get(key, '').encode())
        except (ValueError, TypeError): errors.append(f'{key} must be a Fernet key')
    if config.get('DATA_ENCRYPTION_KEY') == config.get('BACKUP_ENCRYPTION_KEY'):
        errors.append('Use a separate backup encryption key')
    if len(config.get('SECRET_KEY', '')) < 50: errors.append('DJANGO_SECRET_KEY must have at least 50 characters')
    if config.get('SCANNER_MODE') != 'clamav': errors.append('Production requires ClamAV')
    if not config.get('AI_PROVIDER_APPROVED'): errors.append('AI provider approval is required')
    if config.get('AI_ADAPTER') != 'apps.assistant.providers.OllamaProvider':
        errors.append('Configure the implemented approved generative provider adapter')
    model_url=urlparse(config.get('OLLAMA_URL',''))
    if model_url.scheme!='https' and not (model_url.scheme=='http' and model_url.hostname=='ollama'):
        errors.append('OLLAMA_URL must use HTTPS or the isolated ollama container')
    if not config.get('OLLAMA_MODEL'): errors.append('OLLAMA_MODEL is required')
    if '*' in config.get('ALLOWED_HOSTS', []) or any(h in {'localhost','127.0.0.1','testserver'} for h in config.get('ALLOWED_HOSTS', [])):
        errors.append('ALLOWED_HOSTS must list your deployment domains')
    if not config.get('CSRF_TRUSTED_ORIGINS') or any(not o.startswith('https://') or '*' in o for o in config['CSRF_TRUSTED_ORIGINS']):
        errors.append('CSRF_TRUSTED_ORIGINS must list exact HTTPS origins')
    if errors:
        raise ImproperlyConfigured('Production configuration incomplete: ' + '; '.join(errors))
