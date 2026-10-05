"""Run the suite in a disposable, workspace-local PostgreSQL cluster on Windows."""
import os
from pathlib import Path
import secrets
import subprocess
import sys
import uuid
import hashlib
from cryptography.fernet import Fernet
import psycopg
from psycopg import sql
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
BIN = Path(os.environ.get('PG_BIN', r'C:\Program Files\PostgreSQL\18\bin'))
WORK = ROOT / 'var' / 'postgres-verification'
WORK.mkdir(parents=True, exist_ok=True)
password_file = WORK / 'password'
if not password_file.exists():
    password_file.write_text(secrets.token_urlsafe(36), encoding='utf-8')
password = password_file.read_text(encoding='utf-8')
env = dict(os.environ, PGPASSWORD=password, PGHOST='127.0.0.1', PGPORT='55439', PGUSER='verification', PGDATABASE='postgres')
env.update(DATABASE_URL=f'postgresql://verification:{quote(password)}@127.0.0.1:55439/postgres', DATABASE_SSLMODE='disable', DJANGO_DEBUG='true', SYNTHETIC_MODE='true')
env['PATH']=str(BIN)+os.pathsep+env.get('PATH','')

def run(name, *args, **kwargs):
    return subprocess.run([str(BIN / f'{name}.exe'), *args], env=env, check=True, **kwargs)

if not (WORK / 'data' / 'PG_VERSION').exists():
    run('initdb', '-D', str(WORK/'data'), '-U', 'verification', '--auth=scram-sha-256', f'--pwfile={password_file}', '--encoding=UTF8', '--locale=C')
run('pg_ctl', '-D', str(WORK/'data'), '-l', str(WORK/'server.log'), '-o', '-p 55439 -h 127.0.0.1', '-w', 'start')
try:
    result = subprocess.run([sys.executable, str(ROOT/'manage.py'), 'test', 'tests', '--noinput', '--verbosity', '1'], env=env, cwd=ROOT)
    if result.returncode: sys.exit(result.returncode)
    # Fresh databases only: never restore over an existing database.
    suffix=uuid.uuid4().hex[:12]
    source_name=f'backup_source_{suffix}'
    restore_name=f'backup_restore_{suffix}'
    with psycopg.connect(host='127.0.0.1',port=55439,user='verification',password=password,dbname='postgres',autocommit=True) as admin:
        admin.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(source_name)))
        admin.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(restore_name)))
    run_dir=WORK/suffix
    run_dir.mkdir()
    env.update(DATABASE_URL=f'postgresql://verification:{quote(password)}@127.0.0.1:55439/{source_name}',VAR_DIR=str(run_dir),BACKUP_ROOT=str(run_dir/'backups'),BACKUP_ENCRYPTION_KEY=Fernet.generate_key().decode())
    def manage(*args):
        subprocess.run([sys.executable,str(ROOT/'manage.py'),*args],env=env,cwd=ROOT,check=True)
    manage('migrate','--noinput')
    manage('seed_demo','--password',secrets.token_urlsafe(24))
    manage('backup_workspace')
    archive=next((run_dir/'backups').glob('*.backup'))
    recovery=run_dir/'recovered'
    manage('verify_backup',str(archive),'--extract-to',str(recovery))
    restore_env=dict(env,PGDATABASE=restore_name)
    subprocess.run([str(BIN/'pg_restore.exe'),'--dbname',restore_name,'--no-owner','--no-acl','--exit-on-error',str(recovery/'database.dump')],env=restore_env,check=True)
    with psycopg.connect(host='127.0.0.1',port=55439,user='verification',password=password,dbname=restore_name) as restored:
        if restored.execute('SELECT count(*) FROM identity_user').fetchone()[0]!=8: raise RuntimeError('Restored users mismatch')
        versions=restored.execute('SELECT storage_key, sha256 FROM documents_documentversion').fetchall()
        if len(versions)!=2: raise RuntimeError('Restored files mismatch')
        cipher=Fernet((run_dir/'data_encryption_key').read_bytes().strip())
        for storage_key,digest in versions:
            content=cipher.decrypt((recovery/'private'/storage_key).read_bytes())
            if hashlib.sha256(content).hexdigest()!=digest: raise RuntimeError('Restored file hash mismatch')
        if restored.execute("SELECT count(*) FROM pg_trigger WHERE NOT tgisinternal AND tgname LIKE '%tenant_guard'").fetchone()[0]<20: raise RuntimeError('Restored guards missing')
    print('PostgreSQL backup/restore drill passed: users, encrypted file hashes and tenant guards verified.',flush=True)
finally:
    run('pg_ctl', '-D', str(WORK/'data'), '-m', 'fast', '-w', 'stop')
