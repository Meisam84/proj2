from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import RecipientMapping
from .models import ChannelSettings
from django.utils import timezone
from django.core.management import call_command
from io import StringIO

from .models import Alert, ProgramInstance, Schedule
import os

try:
    from twilio.rest import Client as TwilioClient
except Exception:
    TwilioClient = None
try:
    import sentry_sdk
except Exception:
    sentry_sdk = None


@shared_task
def check_alerts_task():
    """Background task that scans for upcoming unapproved program instances and
    creates alerts (same logic as management command check_alerts).
    """
    now = timezone.now()
    window_end = now + timedelta(hours=1)
    instances = ProgramInstance.objects.filter(
        scheduled_start__gte=now,
        scheduled_start__lte=window_end,
        program__evaluation_required=True,
    ).select_related("program")

    created = 0
    for inst in instances:
        if inst.program.evaluation_status == "approved":
            continue
        try:
            sched = inst.schedule
        except Schedule.DoesNotExist:
            continue
        exists = Alert.objects.filter(
            schedule=sched,
            trigger="not_approved_1h",
            sent=False,
        ).exists()
        if exists:
            continue
        msg = (
            f"برنامه '{inst.program.title}' "
            f"برای پخش در {inst.scheduled_start.strftime('%H:%M')} "
            "هنوز تأیید نشده."
        )
        Alert.objects.create(
            trigger="not_approved_1h",
            schedule=sched,
            recipient_roles=["operator", "coordinator", "evaluator"],
            message=msg,
            method="ui",
            sent=False,
        )
        created += 1
    return {"created": created}


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_alert_email(self, alert_id):
    """Send an Alert via email to recipients derived from roles and schedule.

    The task retries up to 3 times on exceptions.
    """
    try:
        alert = Alert.objects.select_related("schedule__program_instance__program").get(pk=alert_id)
    except Alert.DoesNotExist:
        return {"ok": False, "error": "alert_not_found"}

    # Determine recipients from RecipientMapping (admin-configurable) and program members
    roles = alert.recipient_roles or []
    recipients = set()

    # First, add recipients from mappings (these are explicit overrides/extensions)
    try:
        mappings = RecipientMapping.objects.filter(role__code__in=roles, active=True).prefetch_related("persons")
        for m in mappings:
            for p in m.persons.all():
                if p.email:
                    recipients.add(p.email)
            for e in m.emails or []:
                if e:
                    recipients.add(e)
    except Exception:
        # ignore mapping errors and fall back to program members below
        pass

    # Then, include program members that match roles (if any)
    try:
        program = alert.schedule.program_instance.program
        members = program.members.filter(role__code__in=roles).select_related("person", "role")
        for m in members:
            if m.person and m.person.email:
                recipients.add(m.person.email)
    except Exception:
        pass

    # Include conductor contact person if configured
    conductor = getattr(alert.schedule, "conductor", None)
    if conductor and conductor.contact_person and conductor.contact_person.email:
        recipients.add(conductor.contact_person.email)

    recipients = [r for r in recipients if r]
    if not recipients:
        return {"ok": False, "error": "no_recipients"}
    # Determine schedule-level and global channel settings
    sched = alert.schedule
    try:
        cs = ChannelSettings.objects.first()
    except Exception:
        cs = None

    # Respect per-schedule override first
    if not getattr(sched, "email_enabled", lambda: True)():
        return {"ok": False, "error": "email_disabled_by_schedule"}

    subject = f"[هشدار] {alert.get_trigger_display()}"
    message = alert.message
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@example.com")
    # allow ChannelSettings to override default from email if provided
    if cs and cs.default_from_email:
        from_email = cs.default_from_email
    try:
        # render HTML template and plain text fallback
        context = {
            "alert": alert,
            "schedule": getattr(alert, "schedule", None),
            "site_name": getattr(settings, "DEFAULT_FROM_EMAIL", "سامانه کنداکتور"),
        }
        html_message = render_to_string("emails/alert_email.html", context)
        text_message = render_to_string("emails/alert_email.txt", context)

        send_mail(
            subject,
            text_message,
            from_email,
            recipients,
            html_message=html_message,
            fail_silently=False,
        )
    except Exception as exc:  # pragma: no cover - network / SMTP specific
        try:
            raise self.retry(exc=exc)
        except Exception:
            return {"ok": False, "error": str(exc)}

    alert.sent = True
    alert.sent_at = timezone.now()
    alert.save(update_fields=["sent", "sent_at"])
    return {"ok": True, "recipients": len(recipients)}


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_alert_sms(self, alert_id):
    """Send an Alert via SMS using Twilio (if configured).

    If Twilio credentials are not set or `twilio` package is missing, the task
    returns a safe error response instead of raising.
    """
    try:
        alert = Alert.objects.select_related("schedule__program_instance__program").get(pk=alert_id)
    except Alert.DoesNotExist:
        return {"ok": False, "error": "alert_not_found"}

    roles = alert.recipient_roles or []
    recipients = set()

    # Collect phone numbers from RecipientMapping (persons) and program members
    try:
        mappings = RecipientMapping.objects.filter(role__code__in=roles, active=True).prefetch_related("persons")
        for m in mappings:
            for p in m.persons.all():
                if p.phone:
                    recipients.add(p.phone)
    except Exception:
        pass

    try:
        program = alert.schedule.program_instance.program
        members = program.members.filter(role__code__in=roles).select_related("person", "role")
        for m in members:
            if m.person and m.person.phone:
                recipients.add(m.person.phone)
    except Exception:
        pass

    recipients = [r for r in recipients if r]
    if not recipients:
        return {"ok": False, "error": "no_recipients"}

    # Respect per-schedule override first
    sched = alert.schedule
    try:
        cs = ChannelSettings.objects.first()
    except Exception:
        cs = None

    if not getattr(sched, "sms_enabled", lambda: False)():
        return {"ok": False, "error": "sms_disabled_by_schedule"}

    # If Twilio is not configured, return a clear response
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
    from_number = os.environ.get("TWILIO_FROM_NUMBER")
    # allow ChannelSettings to override default from number
    if cs and cs.default_from_number:
        from_number = cs.default_from_number
    if not (TwilioClient and account_sid and auth_token and from_number):
        return {"ok": False, "error": "twilio_not_configured"}

    try:
        client = TwilioClient(account_sid, auth_token)
        body = alert.message
        sent = 0
        for to in recipients:
            client.messages.create(body=body, from_=from_number, to=to)
            sent += 1
    except Exception as exc:  # pragma: no cover - external network
        # Report to Sentry if available, then retry
        if sentry_sdk:
            sentry_sdk.capture_exception(exc)
        try:
            raise self.retry(exc=exc)
        except Exception:
            return {"ok": False, "error": str(exc)}

    alert.sent = True
    alert.sent_at = timezone.now()
    alert.save(update_fields=["sent", "sent_at"])
    return {"ok": True, "sent": sent}


@shared_task
def run_scheduled_e2e_task():
    """Wrapper task to run scheduled E2E via management command.

    This allows Celery Beat to schedule evaluation of `E2ESchedule` entries
    without requiring an external cron.
    """
    sio = StringIO()
    try:
        call_command("run_scheduled_e2e", stdout=sio)
    except Exception as exc:  # pragma: no cover - external
        # Log or report to Sentry if available
        try:
            import sentry_sdk

            sentry_sdk.capture_exception(exc)
        except Exception:
            pass
    return sio.getvalue()
