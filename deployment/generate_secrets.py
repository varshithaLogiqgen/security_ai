"""Generate local deployment secret files once. Never overwrite existing keys."""
from pathlib import Path
import secrets
from cryptography.fernet import Fernet

root = Path(__file__).resolve().parent / 'secrets'
root.mkdir(mode=0o700, exist_ok=True)
def create(name, factory):
    path = root / name
    try:
        with path.open('x', encoding='utf-8') as out: out.write(factory())
        path.chmod(0o600)
    except FileExistsError: pass
    return path.read_text(encoding='utf-8').strip()

owner = create('postgres_password', lambda:secrets.token_urlsafe(48))
app = create('app_password', lambda:secrets.token_urlsafe(48))
create('django_secret',lambda:secrets.token_urlsafe(64))
create('encryption_key',lambda:Fernet.generate_key().decode())
create('backup_key',lambda:Fernet.generate_key().decode())
create('database_url',lambda:f'postgresql://secureai_app:{app}@db:5432/secureai')
create('migration_database_url',lambda:f'postgresql://secureai_owner:{owner}@db:5432/secureai')
create('oidc_secret',lambda:'')
create('ollama_key',lambda:'')
print('Secret files prepared without overwriting existing values. Supply the OIDC secret before deployment. Keep key backups in your secret manager.')
