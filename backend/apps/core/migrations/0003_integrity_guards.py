"""Tenant checks and immutable records enforced even for bulk SQL writes."""
from django.db import migrations

APP_LABELS={'identity','projects','work_updates','people','documents','assistant','notifications','administration','audit','core'}
IMMUTABLE={'audit_auditevent','documents_documentversion','work_updates_updaterevision'}

def install(apps,schema_editor):
    vendor=schema_editor.connection.vendor
    if vendor not in {'sqlite','postgresql'}: raise RuntimeError('Unsupported database for security guards.')
    quote=schema_editor.quote_name
    for model in apps.get_models():
        if model._meta.app_label not in APP_LABELS: continue
        table=model._meta.db_table
        fields={f.name:f for f in model._meta.fields}
        if 'organization' not in fields: continue
        checks=[]
        for field in model._meta.fields:
            related=getattr(field,'related_model',None)
            if related and field.name!='organization' and any(f.name=='organization' for f in related._meta.fields):
                checks.append(f'(NEW.{quote(field.column)} IS NOT NULL AND NEW.organization_id <> (SELECT organization_id FROM {quote(related._meta.db_table)} WHERE id=NEW.{quote(field.column)}))')
        if table=='documents_document':
            checks.append('(NEW.current_version_id IS NOT NULL AND NEW.id <> (SELECT document_id FROM documents_documentversion WHERE id=NEW.current_version_id))')
        if 'valid_from' in fields:
            checks.append('(NEW.valid_to IS NOT NULL AND NEW.valid_to <= NEW.valid_from)')
        predicate=' OR '.join(checks) or '1=0'
        if vendor=='sqlite':
            for event in ['INSERT','UPDATE']:
                condition=predicate+((' OR OLD.organization_id <> NEW.organization_id') if event=='UPDATE' else '')
                name=f'{table}_tenant_{event.lower()}'
                schema_editor.execute(f'CREATE TRIGGER {quote(name)} BEFORE {event} ON {quote(table)} WHEN {condition} BEGIN SELECT RAISE(ABORT, \'tenant_integrity\'); END;')
            if table in IMMUTABLE:
                for event in ['UPDATE','DELETE']:
                    schema_editor.execute(f'CREATE TRIGGER {quote(table+"_immutable_"+event.lower())} BEFORE {event} ON {quote(table)} BEGIN SELECT RAISE(ABORT, \'immutable_record\'); END;')
        else:
            name=table+'_tenant_guard'
            schema_editor.execute(f'''CREATE FUNCTION {quote(name)}() RETURNS trigger AS $$ BEGIN
              IF {predicate} THEN RAISE EXCEPTION 'tenant_integrity' USING ERRCODE = '23514'; END IF;
              IF TG_OP = 'UPDATE' AND OLD.organization_id <> NEW.organization_id THEN RAISE EXCEPTION 'immutable_tenant' USING ERRCODE = '23514'; END IF;
              RETURN NEW; END; $$ LANGUAGE plpgsql;''')
            schema_editor.execute(f'CREATE TRIGGER {quote(name)} BEFORE INSERT OR UPDATE ON {quote(table)} FOR EACH ROW EXECUTE FUNCTION {quote(name)}();')
            if table in IMMUTABLE:
                name=table+'_immutable_guard'
                schema_editor.execute(f"CREATE FUNCTION {quote(name)}() RETURNS trigger AS $$ BEGIN RAISE EXCEPTION 'immutable_record' USING ERRCODE = '23514'; END; $$ LANGUAGE plpgsql;")
                schema_editor.execute(f'CREATE TRIGGER {quote(name)} BEFORE UPDATE OR DELETE ON {quote(table)} FOR EACH ROW EXECUTE FUNCTION {quote(name)}();')
    if vendor=='postgresql':
        schema_editor.execute("CREATE INDEX protected_chunk_search ON documents_documentchunk USING GIN (to_tsvector('english', text));")
        schema_editor.execute("CREATE INDEX protected_update_search ON work_updates_workupdate USING GIN (to_tsvector('english', body));")

def uninstall(apps,schema_editor):
    quote=schema_editor.quote_name
    for model in apps.get_models():
        table=model._meta.db_table
        if model._meta.app_label not in APP_LABELS or not any(f.name=='organization' for f in model._meta.fields): continue
        if schema_editor.connection.vendor=='sqlite':
            for suffix in ['tenant_insert','tenant_update','immutable_update','immutable_delete']:
                schema_editor.execute(f'DROP TRIGGER IF EXISTS {quote(table+"_"+suffix)};')
        else:
            for suffix in ['tenant_guard','immutable_guard']:
                schema_editor.execute(f'DROP TRIGGER IF EXISTS {quote(table+"_"+suffix)} ON {quote(table)};')
                schema_editor.execute(f'DROP FUNCTION IF EXISTS {quote(table+"_"+suffix)}();')
    if schema_editor.connection.vendor=='postgresql':
        schema_editor.execute('DROP INDEX IF EXISTS protected_chunk_search;')
        schema_editor.execute('DROP INDEX IF EXISTS protected_update_search;')

class Migration(migrations.Migration):
    dependencies=[('core','0002_initial'),('identity','0001_initial'),('projects','0001_initial'),('work_updates','0001_initial'),('people','0001_initial'),('documents','0002_initial'),('assistant','0002_initial'),('notifications','0001_initial'),('administration','0002_initial'),('audit','0002_initial')]
    operations=[migrations.RunPython(install,uninstall)]

