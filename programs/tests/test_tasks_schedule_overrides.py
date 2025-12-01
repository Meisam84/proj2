from django.test import TestCase, override_settings
from django.utils import timezone
from datetime import timedelta
import os
from unittest.mock import patch

from programs.models import (
    Channel,
    Role,
    Person,
    Program,
    ProgramMember,
    ProgramInstance,
    Schedule,
    Alert,
    ChannelSettings,
)
from programs import tasks as tasks_module
from programs.tasks import send_alert_email
from django.core import mail


class TaskScheduleOverrideTests(TestCase):
    def setUp(self):
        self.channel = Channel.objects.create(name="C", code="C1", program_type="radio")
        self.role = Role.objects.create(name="Producer", code="producer")
        self.person = Person.objects.create(full_name="Ali", email="ali@example.com", phone="+10000000000")
        self.program = Program.objects.create(title="P", channel=self.channel, default_duration=timedelta(minutes=30))
        ProgramMember.objects.create(program=self.program, person=self.person, role=self.role)

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_send_alert_email_respects_schedule_disable(self):
        start = timezone.now() + timedelta(minutes=30)
        pi = ProgramInstance.objects.create(
            program=self.program,
            scheduled_start=start,
            scheduled_end=start + self.program.default_duration,
            status="pending",
        )
        sched = Schedule.objects.create(program_instance=pi, channel=self.channel, schedule_date=start.date(), order=1)
        # explicitly disable email for this schedule
        sched.override_enable_email = "disabled"
        sched.save()

        alert = Alert.objects.create(
            trigger="not_approved_1h",
            schedule=sched,
            recipient_roles=[self.role.code],
            message="Test message",
            method="email",
        )

        result = send_alert_email(alert.id)
        self.assertFalse(result.get("ok"))
        self.assertEqual(result.get("error"), "email_disabled_by_schedule")
        # no email sent
        self.assertEqual(len(mail.outbox), 0)
        alert.refresh_from_db()
        self.assertFalse(alert.sent)

    def test_send_alert_sms_respects_schedule_disable(self):
        start = timezone.now() + timedelta(minutes=30)
        pi = ProgramInstance.objects.create(
            program=self.program,
            scheduled_start=start,
            scheduled_end=start + self.program.default_duration,
            status="pending",
        )
        sched = Schedule.objects.create(program_instance=pi, channel=self.channel, schedule_date=start.date(), order=1)
        # explicitly disable sms for this schedule
        sched.override_enable_sms = "disabled"
        sched.save()

        alert = Alert.objects.create(
            trigger="not_approved_1h",
            schedule=sched,
            recipient_roles=[self.role.code],
            message="Test SMS",
            method="sms",
        )

        # Patch TwilioClient to ensure configuration would otherwise work
        class FakeMessages:
            def __init__(self):
                self.created = []

            def create(self, body, from_, to):
                self.created.append((body, from_, to))

        class FakeClient:
            def __init__(self, sid, token):
                self.messages = FakeMessages()

        with patch.object(tasks_module, "TwilioClient", FakeClient):
            with patch.dict(os.environ, {"TWILIO_ACCOUNT_SID": "sid", "TWILIO_AUTH_TOKEN": "token", "TWILIO_FROM_NUMBER": "+19999999999"}):
                res = tasks_module.send_alert_sms(alert.id)

        self.assertFalse(res.get("ok"))
        self.assertEqual(res.get("error"), "sms_disabled_by_schedule")
        alert.refresh_from_db()
        self.assertFalse(alert.sent)
