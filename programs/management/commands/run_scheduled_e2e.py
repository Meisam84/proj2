from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime

from programs.models import E2ESchedule
from django.core.management import call_command
from io import StringIO
import json


class Command(BaseCommand):
    help = "Run enabled E2E schedules (intended to be run from cron or Celery Beat)."

    def handle(self, *args, **options):
        now = timezone.localtime()
        runs = 0
        for sched in E2ESchedule.objects.filter(enabled=True):
            should_run = False
            if sched.schedule_type == "hourly":
                should_run = True
            elif sched.schedule_type == "daily":
                if sched.time_of_day:
                    # compare hour and minute
                    tod = sched.time_of_day
                    if now.hour == tod.hour and now.minute == tod.minute:
                        should_run = True
            elif sched.schedule_type == "weekly":
                if sched.time_of_day is not None and sched.day_of_week is not None:
                    tod = sched.time_of_day
                    if now.weekday() == sched.day_of_week and now.hour == tod.hour and now.minute == tod.minute:
                        should_run = True

            if should_run:
                # run the management command and record output to stdout
                sio = StringIO()
                try:
                    call_command("send_test_alert", "--create", f"--method={sched.method}", stdout=sio)
                    out = sio.getvalue()
                    # print result summary
                    for line in out.splitlines():
                        if line.startswith("E2E_RESULT:"):
                            try:
                                parsed = json.loads(line.split("E2E_RESULT:", 1)[1].strip())
                                self.stdout.write(
                                    f"Schedule {sched.name}: ok={parsed.get('ok')}, recipients={parsed.get('recipients')}"
                                )
                            except Exception:
                                self.stdout.write(f"Schedule {sched.name}: raw output: {line}")
                    runs += 1
                except Exception as exc:
                    self.stderr.write(str(exc))

        self.stdout.write(f"Scheduled E2E runs processed: {runs}")
