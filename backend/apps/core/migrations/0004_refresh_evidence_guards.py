from importlib import import_module
from django.db import migrations


def refresh(apps, schema_editor):
    # SQLite may rebuild tables for AddField, removing their custom triggers.
    guards = import_module('apps.core.migrations.0003_integrity_guards')
    guards.uninstall(apps, schema_editor)
    guards.install(apps, schema_editor)
    # Older answers recorded citations only, so their full context is unknown.
    apps.get_model('assistant', 'Message').objects.update(state='access_changed', answer='')


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0003_integrity_guards'),
        ('assistant', '0003_answersource_is_citation'),
    ]
    operations = [migrations.RunPython(refresh, migrations.RunPython.noop)]
