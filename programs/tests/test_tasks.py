from datetime import timedelta

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from programs.models import Alert, Channel, Program, ProgramInstance, Schedule
from programs.tasks import check_alerts_task


class AlertTaskTests(TestCase):
    def setUp(self):
        self.channel = Channel.objects.create(
            name="TestChannel",
            code="TC1",
            program_type="radio",
            timezone="Asia/Tehran",
        )
        self.program = Program.objects.create(
            title="Test Program",
            channel=self.channel,
            evaluation_required=True,
            default_duration=timedelta(minutes=30),
        )

    def test_check_alerts_creates_alert(self):
        start = timezone.now() + timedelta(minutes=30)
        end = start + self.program.default_duration
        pi = ProgramInstance.objects.create(
            program=self.program,
            scheduled_start=start,
            scheduled_end=end,
            status="pending",
        )
        Schedule.objects.create(
            program_instance=pi,
            channel=self.channel,
            schedule_date=start.date(),
            order=1,
        )

        # ensure no alerts initially
        self.assertEqual(Alert.objects.count(), 0)

        # run task synchronously
        result = check_alerts_task.run()
        self.assertIsInstance(result, dict)
        self.assertGreaterEqual(result.get("created", 0), 1)
        self.assertEqual(Alert.objects.count(), 1)

    def test_management_command_creates_alert(self):
        start = timezone.now() + timedelta(minutes=30)
        end = start + self.program.default_duration
        pi = ProgramInstance.objects.create(
            program=self.program,
            scheduled_start=start,
            scheduled_end=end,
            status="pending",
        )
        Schedule.objects.create(
            program_instance=pi,
            channel=self.channel,
            schedule_date=start.date(),
            order=1,
        )

        # call management command
        call_command("check_alerts")

        self.assertEqual(Alert.objects.count(), 1)
