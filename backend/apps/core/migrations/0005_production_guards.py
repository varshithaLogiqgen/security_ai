from importlib import import_module
from django.db import migrations


def refresh(apps, schema_editor):
    guards=import_module('apps.core.migrations.0003_integrity_guards')
    guards.uninstall(apps,schema_editor)
    guards.install(apps,schema_editor)


class Migration(migrations.Migration):
    dependencies=[('core','0004_refresh_evidence_guards'),('assistant','0004_conversation_legal_hold'),('documents','0003_document_purged_at')]
    operations=[migrations.RunPython(refresh,migrations.RunPython.noop)]
