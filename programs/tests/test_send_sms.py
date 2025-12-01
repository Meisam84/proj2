from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
import os
from unittest.mock import patch

from programs.models import Channel, Role, Person, Program, ProgramMember, ProgramInstance, Schedule, Alert
from programs import tasks as tasks_module


class SendAlertSMSTests(TestCase):
    def setUp(self):
        self.channel = Channel.objects.create(name="C", code="C1", program_type="radio")
        self.role = Role.objects.create(name="Producer", code="producer")
        self.person = Person.objects.create(full_name="Ali", phone="+10000000000")
        self.program = Program.objects.create(title="P", channel=self.channel, default_duration=timedelta(minutes=30))
        ProgramMember.objects.create(program=self.program, person=self.person, role=self.role)

    def _create_alert(self, minutes_from_now=30, method="sms"):
        start = timezone.now() + timedelta(minutes=minutes_from_now)
        pi = ProgramInstance.objects.create(
            program=self.program,
            scheduled_start=start,
            scheduled_end=start + self.program.default_duration,
            status="pending",
        )
        Schedule.objects.create(program_instance=pi, channel=self.channel, schedule_date=start.date(), order=1)
        alert = Alert.objects.create(
            trigger="not_approved_1h",
            schedule=pi.schedule,
            recipient_roles=[self.role.code],
            message="Test SMS",
            method=method,
        )
        return alert

    def test_sms_not_configured_returns_error(self):
        alert = self._create_alert()
        # Ensure Twilio client is treated as missing / env not set
        with patch.object(tasks_module, "TwilioClient", None):
            with patch.dict(os.environ, {"TWILIO_ACCOUNT_SID": "", "TWILIO_AUTH_TOKEN": "", "TWILIO_FROM_NUMBER": ""}):
                res = tasks_module.send_alert_sms(alert.id)
        self.assertFalse(res.get("ok"))
        self.assertEqual(res.get("error"), "twilio_not_configured")

    def test_sms_send_marks_alert_sent(self):
        alert = self._create_alert()

        class FakeMessages:
            def __init__(self):
                self.created = []

            def create(self, body, from_, to):
                self.created.append((body, from_, to))

        class FakeClient:
            def __init__(self, sid, token):
                self.messages = FakeMessages()

        with patch.object(tasks_module, "TwilioClient", FakeClient):
            with patch.dict(
                os.environ,
                {"TWILIO_ACCOUNT_SID": "sid", "TWILIO_AUTH_TOKEN": "token", "TWILIO_FROM_NUMBER": "+19999999999"},
            ):
                res = tasks_module.send_alert_sms(alert.id)

        self.assertTrue(res.get("ok"))
        self.assertEqual(res.get("sent"), 1)
        alert.refresh_from_db()
        self.assertTrue(alert.sent)
        self.assertIsNotNone(alert.sent_at)
