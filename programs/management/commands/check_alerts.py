from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from programs.models import Alert, ProgramInstance, Schedule


class Command(BaseCommand):
    help = "Scan upcoming schedules and create alerts for unapproved items (e.g. not approved 1 hour before start)"

    def handle(self, *args, **options):
        now = timezone.now()
        window_end = now + timedelta(hours=1)

        # Find program instances that require evaluation and whose parent program is not approved
        instances = ProgramInstance.objects.filter(
            scheduled_start__gte=now,
            scheduled_start__lte=window_end,
            program__evaluation_required=True,
        ).select_related("program")

        created = 0
        for inst in instances:
            # If program is approved, skip
            if inst.program.evaluation_status == "approved":
                continue

            # check schedule
            try:
                sched = inst.schedule
            except Schedule.DoesNotExist:
                continue

            # avoid duplicate similar alerts for same schedule & trigger
            exists = Alert.objects.filter(schedule=sched, trigger="not_approved_1h", sent=False).exists()
            if exists:
                continue

            msg = f"برنامه '{inst.program.title}' برای پخش در {inst.scheduled_start.strftime('%H:%M')} هنوز تأیید نشده."
            Alert.objects.create(
                trigger="not_approved_1h",
                schedule=sched,
                recipient_roles=["operator", "coordinator", "evaluator"],
                message=msg,
                method="ui",
                sent=False,
            )
            created += 1

        self.stdout.write(self.style.SUCCESS(f"Alerts created: {created}"))
