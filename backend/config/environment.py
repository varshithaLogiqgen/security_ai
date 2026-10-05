"""Read secrets from a secret manager's mounted files or environment variables."""
import os
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured


def value(name, default=''):
    filename = os.getenv(f'{name}_FILE')
    if filename:
        if os.getenv(name):
            raise ImproperlyConfigured(f'Set either {name} or {name}_FILE, not both.')
        try:
            return Path(filename).read_text(encoding='utf-8').strip()
        except OSError:
            raise ImproperlyConfigured(f'Cannot read {name}_FILE.') from None
    return os.getenv(name, default)
