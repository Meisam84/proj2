from django.test import TestCase, override_settings
from django.utils import timezone
from datetime import timedelta

from programs.models import Channel, Program, ProgramInstance, Schedule, Alert, Person, ProgramMember, Role
from programs.tasks import send_alert_email
from django.core import mail


class SendAlertEmailTests(TestCase):
    def setUp(self):
        self.channel = Channel.objects.create(name="C", code="C1", program_type="radio")
        self.role = Role.objects.create(name="Producer", code="producer")
        self.person = Person.objects.create(full_name="Ali", email="ali@example.com")
        self.program = Program.objects.create(title="P", channel=self.channel, default_duration=timedelta(minutes=30))
        pm = ProgramMember.objects.create(program=self.program, person=self.person, role=self.role)

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_send_alert_email_marks_sent(self):
        start = timezone.now() + timedelta(minutes=30)
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
            message="Test message",
            method="email",
        )

        result = send_alert_email(alert.id)
        self.assertTrue(result.get("ok"))
        # one email sent
        self.assertEqual(len(mail.outbox), 1)
        alert.refresh_from_db()
        self.assertTrue(alert.sent)
        self.assertIsNotNone(alert.sent_at)
