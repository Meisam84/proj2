from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from programs.models import Channel, Role, Person, Program, ProgramMember, ProgramInstance, Schedule, Alert
from programs import tasks
import json


class Command(BaseCommand):
    help = "Create a test Alert and run send_alert_email/send_alert_sms tasks synchronously (for local testing)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--create",
            action="store_true",
            help="Create sample Channel/Program/Role/Person if none exist",
        )
        parser.add_argument(
            "--method",
            choices=["email", "sms", "both"],
            default="email",
            help="Which channel(s) to run (default: email)",
        )
        parser.add_argument(
            "--override-email",
            choices=["inherit", "enabled", "disabled"],
            default=None,
            help="Optional: set schedule.override_enable_email for the created schedule",
        )
        parser.add_argument(
            "--override-sms",
            choices=["inherit", "enabled", "disabled"],
            default=None,
            help="Optional: set schedule.override_enable_sms for the created schedule",
        )

    def handle(self, *args, **options):
        if options["create"]:
            channel, _ = Channel.objects.get_or_create(name="TestChannel", code="TEST", program_type="radio")
            role, _ = Role.objects.get_or_create(name="TestRole", code="testrole")
            person, _ = Person.objects.get_or_create(
                full_name="Test Person", email="test@example.com", phone="+10000000000"
            )
            program, _ = Program.objects.get_or_create(
                title="Test Program",
                channel=channel,
                defaults={"default_duration": timedelta(minutes=30), "description": "test"},
            )
            ProgramMember.objects.get_or_create(program=program, person=person, role=role)
        else:
            channel = Channel.objects.first()
            role = Role.objects.first()
            person = Person.objects.first()
            program = Program.objects.first()

        if not (channel and role and person and program):
            self.stdout.write(self.style.ERROR("Missing required objects. Use --create to create sample data."))
            return

        # create a ProgramInstance + Schedule
        start = timezone.now() + timedelta(minutes=30)
        pi = ProgramInstance.objects.create(
            program=program, scheduled_start=start, scheduled_end=start + program.default_duration, status="pending"
        )
        sched = Schedule.objects.create(program_instance=pi, channel=channel, schedule_date=start.date(), order=1)
        # apply optional overrides provided by the caller (useful for E2E tests)
        if options.get("override_email"):
            sched.override_enable_email = options.get("override_email")
            sched.save(update_fields=["override_enable_email"])
        if options.get("override_sms"):
            sched.override_enable_sms = options.get("override_sms")
            sched.save(update_fields=["override_enable_sms"])

        alert = Alert.objects.create(
            trigger="not_approved_1h",
            schedule=sched,
            recipient_roles=[role.code],
            message="Test alert message",
            method="email",
        )

        methods = []
        if options["method"] in ("email", "both"):
            methods.append("email")
        if options["method"] in ("sms", "both"):
            methods.append("sms")

        for m in methods:
            if m == "email":
                self.stdout.write("Running send_alert_email (synchronously via apply)...")
                res = tasks.send_alert_email.apply(args=[alert.id])
                result = res.get()
                # print a machine-readable JSON marker for easy parsing by admin
                self.stdout.write(f"E2E_RESULT: {json.dumps(result, default=str)}")
            if m == "sms":
                self.stdout.write("Running send_alert_sms (synchronously via apply)...")
                res = tasks.send_alert_sms.apply(args=[alert.id])
                result = res.get()
                self.stdout.write(f"E2E_RESULT: {json.dumps(result, default=str)}")

        self.stdout.write(self.style.SUCCESS("Test alert processing complete."))
