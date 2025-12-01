from django.test import TestCase, RequestFactory
from programs.admin import ScheduleAdmin
from django.contrib import admin
from programs.models import Channel, Program, ProgramInstance, Schedule
from datetime import timedelta, date, datetime


class ScheduleAdminActionsTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.channel = Channel.objects.create(name="C", code="C1", program_type="radio")
        program = Program.objects.create(title="P", channel=self.channel, default_duration=timedelta(minutes=30))
        pi1 = ProgramInstance.objects.create(program=program, scheduled_start=datetime.now(), scheduled_end=datetime.now()+timedelta(hours=1))
        pi2 = ProgramInstance.objects.create(program=program, scheduled_start=datetime.now()+timedelta(days=1), scheduled_end=datetime.now()+timedelta(days=1, hours=1))
        self.s1 = Schedule.objects.create(channel=self.channel, schedule_date=date.today(), program_instance=pi1, order=1)
        self.s2 = Schedule.objects.create(channel=self.channel, schedule_date=date.today(), program_instance=pi2, order=2)
        self.admin = ScheduleAdmin(Schedule, admin.site)

    def _make_request(self):
        req = self.factory.post("/admin/programs/schedule/", {})
        # attach messages storage used by admin.message_user
        from django.contrib.messages.storage.fallback import FallbackStorage

        setattr(req, "session", {})
        setattr(req, "_messages", FallbackStorage(req))
        return req

    def test_bulk_set_email_disable(self):
        req = self._make_request()
        qs = Schedule.objects.filter(id__in=[self.s1.id, self.s2.id])
        self.admin.set_email_override_disabled(req, qs)
        self.s1.refresh_from_db()
        self.s2.refresh_from_db()
        self.assertEqual(self.s1.override_enable_email, "disabled")
        self.assertEqual(self.s2.override_enable_email, "disabled")

    def test_bulk_set_sms_enable(self):
        req = self._make_request()
        qs = Schedule.objects.filter(id__in=[self.s1.id])
        self.admin.set_sms_override_enabled(req, qs)
        self.s1.refresh_from_db()
        self.assertEqual(self.s1.override_enable_sms, "enabled")
