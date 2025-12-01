from django.test import TestCase
from django.core.management import call_command
from io import StringIO
import json


class SendTestAlertCommandIntegrationTests(TestCase):
    def test_send_test_alert_respects_override_email_disabled(self):
        out = StringIO()
        # create sample data and set schedule override to disabled
        call_command("send_test_alert", "--create", "--method=email", "--override-email=disabled", stdout=out)
        output = out.getvalue()
        # parse the E2E_RESULT JSON line
        parsed = None
        for line in output.splitlines():
            if line.startswith("E2E_RESULT:"):
                parsed = json.loads(line.split("E2E_RESULT:", 1)[1].strip())
        self.assertIsNotNone(parsed)
        self.assertFalse(parsed.get("ok"))
        self.assertEqual(parsed.get("error"), "email_disabled_by_schedule")

    def test_send_test_alert_respects_override_sms_disabled(self):
        out = StringIO()
        call_command("send_test_alert", "--create", "--method=sms", "--override-sms=disabled", stdout=out)
        output = out.getvalue()
        parsed = None
        for line in output.splitlines():
            if line.startswith("E2E_RESULT:"):
                parsed = json.loads(line.split("E2E_RESULT:", 1)[1].strip())
        self.assertIsNotNone(parsed)
        self.assertFalse(parsed.get("ok"))
        self.assertEqual(parsed.get("error"), "sms_disabled_by_schedule")
