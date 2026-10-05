import os
from unittest import skipUnless
from django.test import SimpleTestCase, override_settings
from apps.core.management.commands.production_verify import Command


@skipUnless(os.getenv('RUN_CLAMAV_INTEGRATION')=='true','Requires running ClamAV with current signatures')
@override_settings(SCANNER_MODE='clamav')
class LiveScannerTests(SimpleTestCase):
    def test_clean_sample_and_eicar_with_current_signatures(self):
        Command().scanner()
