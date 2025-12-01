from django.test import TestCase

from ..models import Schedule, Channel, Program, ProgramInstance, ChannelSettings
from datetime import date, timedelta
from django.utils import timezone


class ScheduleOverrideTests(TestCase):
    def setUp(self):
        # minimal objects required to create a Schedule
        self.channel = Channel.objects.create(name="C1", code="C1", program_type="radio")
        program = Program.objects.create(
            title="P1",
            description="desc",
            channel=self.channel,
            default_duration=timedelta(minutes=60),
        )
        pi = ProgramInstance.objects.create(
            program=program,
            scheduled_start=timezone.now(),
            scheduled_end=timezone.now() + timedelta(hours=1),
        )
        self.schedule = Schedule.objects.create(channel=self.channel, schedule_date=date.today(), program_instance=pi, order=1)

    def test_defaults_when_no_channelsettings(self):
        # No ChannelSettings object exists: email should default True, sms defaults to True
        # (older behavior allowed SMS sending when no ChannelSettings row exists).
        self.assertEqual(self.schedule.override_enable_email, "inherit")
        self.assertTrue(self.schedule.email_enabled())
        self.assertTrue(self.schedule.sms_enabled())

    def test_respect_channelsettings_when_inherit(self):
        # Create channel settings with non-defaults and ensure inherit uses them
        ChannelSettings.objects.create(enable_email=False, enable_sms=True)
        s = Schedule.objects.get(pk=self.schedule.pk)
        self.assertFalse(s.email_enabled())
        self.assertTrue(s.sms_enabled())

    def test_schedule_overrides_precedence(self):
        # Even if ChannelSettings says email disabled, schedule override 'enabled' forces it
        ChannelSettings.objects.create(enable_email=False, enable_sms=False)
        s = Schedule.objects.get(pk=self.schedule.pk)
        s.override_enable_email = "enabled"
        s.override_enable_sms = "disabled"
        s.save()
        s.refresh_from_db()
        self.assertTrue(s.email_enabled())
        self.assertFalse(s.sms_enabled())
