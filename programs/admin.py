import io

from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

try:
    import openpyxl
    from openpyxl.utils import get_column_letter
except Exception:
    openpyxl = None

# Avoid importing WeasyPrint at module import time because it prints
# native-dependency diagnostic messages (and may require system libs).
# Import it lazily inside the admin action where it's actually used.
HTML = None
from .models import (
    Alert,
    AnalyticsData,
    Channel,
    Conductor,
    ConductorLog,
    Evaluation,
    Genre,
    LiveSegment,
    Person,
    Program,
    ProgramAsset,
    ProgramGuest,
    ProgramInstance,
    ProgramMember,
    ProgramVersion,
    RecipientMapping,
    ChannelSettings,
    E2ERun,
    ReplacementRule,
    Role,
    Schedule,
    ScheduleModification,
    ScheduleTemplate,
    TargetAudience,
)

# ============================================================================
# بخش 1: اطلاعات مرجع
# ============================================================================


@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "program_type", "is_active", "latitude", "longitude", "timezone")
    search_fields = ("name", "code")
    list_filter = ("program_type", "is_active")


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ("name", "code")
    search_fields = ("name", "code")


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("name", "code")
    search_fields = ("name", "code")


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "phone", "is_active")
    search_fields = ("full_name", "email", "phone")
    list_filter = ("is_active", "created_at")


@admin.register(TargetAudience)
class TargetAudienceAdmin(admin.ModelAdmin):
    list_display = ("name", "age_min", "age_max")
    search_fields = ("name",)


# ============================================================================
# بخش 2: اطلاعات برنامه
# ============================================================================


class ProgramMemberInline(admin.TabularInline):
    model = ProgramMember
    extra = 1


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "channel",
        "broadcast_type",
        "program_origin",
        "media_source",
        "default_duration",
        "is_live",
        "is_repeatable",
        "is_active",
    )
    search_fields = ("title", "subtitle", "description")
    list_filter = ("channel", "is_live", "is_repeatable", "is_active", "genres", "target_audiences")
    inlines = [ProgramMemberInline]


# ============================================================================
# بخش 3: نمونه‌های برنامه
# ============================================================================


class ProgramGuestInline(admin.TabularInline):
    model = ProgramGuest
    extra = 1


class ProgramAssetInline(admin.TabularInline):
    model = ProgramAsset
    extra = 1


@admin.register(ProgramInstance)
class ProgramInstanceAdmin(admin.ModelAdmin):
    list_display = (
        "program",
        "episode_number",
        "scheduled_start",
        "scheduled_end",
        "status",
        "submitted_at",
        "approved_at",
    )
    search_fields = ("program__title", "episode_title")
    list_filter = ("status", "program", "scheduled_start")
    inlines = [ProgramGuestInline, ProgramAssetInline]
    readonly_fields = ("created_at", "updated_at")


@admin.register(ProgramGuest)
class ProgramGuestAdmin(admin.ModelAdmin):
    list_display = ("program_instance", "person", "guest_order")
    search_fields = ("program_instance__program__title", "person__full_name")
    list_filter = ("program_instance__program__channel",)


@admin.register(ProgramAsset)
class ProgramAssetAdmin(admin.ModelAdmin):
    list_display = ("title", "program_instance", "asset_type", "uploaded_at")
    search_fields = ("title", "program_instance__program__title")
    list_filter = ("asset_type", "uploaded_at")
    readonly_fields = ("uploaded_at",)


# ============================================================================
# بخش 4: ویرایش و نسخه‌ها
# ============================================================================


@admin.register(ProgramVersion)
class ProgramVersionAdmin(admin.ModelAdmin):
    list_display = ("program_instance", "version_number", "created_at", "created_by")
    search_fields = ("program_instance__program__title",)
    list_filter = ("created_at",)
    readonly_fields = ("created_at",)


@admin.register(ScheduleModification)
class ScheduleModificationAdmin(admin.ModelAdmin):
    list_display = ("program_instance", "modification_type", "created_at", "created_by")
    search_fields = ("program_instance__program__title",)
    list_filter = ("modification_type", "created_at")
    readonly_fields = ("created_at",)


# ============================================================================
# بخش 5: مدیریت و کنداکتور
# ============================================================================


class ConductorInline(admin.StackedInline):
    model = Conductor
    extra = 0


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    def override_info(self, obj=None):
        html = """
        <div style="padding:10px;border-left:4px solid #3b82f6;background:#f0f9ff;margin-bottom:10px;">
            <strong>بازنویسی کانال‌ها (Per-schedule)</strong>
            <div style="margin-top:6px;">قواعد: <em>Schedule override</em> &gt; <em>ChannelSettings</em> &gt; <em>defaults</em>.
            اگر برای این برنامه‌ریزی مقدار روی <strong>غیرفعال</strong> تنظیم شود، ارسال آن کانال (ایمیل/پیامک)
            متوقف می‌شود.</div>
        </div>
        """
        return mark_safe(html)

    override_info.short_description = "اطلاعیهٔ بازنویسی کانال‌ها"
    list_display = (
        "program_instance",
        "channel",
        "schedule_date",
        "order",
        "is_active",
        "locked",
        "initial_version",
        "updated_version",
        "override_enable_email",
        "override_enable_sms",
    )
    search_fields = ("program_instance__program__title",)
    list_filter = ("channel", "schedule_date", "is_active", "override_enable_email", "override_enable_sms")
    list_editable = ("override_enable_email", "override_enable_sms")
    inlines = [ConductorInline]
    readonly_fields = ("created_at", "updated_at")
    # Show override controls in the change form so admins can set them per-schedule
    fields = (
        "override_info",
        "channel",
        "schedule_date",
        "program_instance",
        "order",
        "is_active",
        "locked",
        "initial_version",
        "updated_version",
        "notes",
        ("override_enable_email", "override_enable_sms"),
        "created_at",
        "updated_at",
    )
    actions = ("export_schedule_xlsx", "export_schedule_pdf")
    # Bulk actions to apply per-schedule override values quickly and safely
    def _bulk_set_override(self, request, queryset, field_name, value):
        updated = queryset.update(**{field_name: value})
        self.message_user(request, f"Updated {updated} schedule(s): set {field_name}={value}")

    def set_email_override_enabled(self, request, queryset):
        return self._bulk_set_override(request, queryset, "override_enable_email", "enabled")

    def set_email_override_disabled(self, request, queryset):
        return self._bulk_set_override(request, queryset, "override_enable_email", "disabled")

    def set_email_override_inherit(self, request, queryset):
        return self._bulk_set_override(request, queryset, "override_enable_email", "inherit")

    def set_sms_override_enabled(self, request, queryset):
        return self._bulk_set_override(request, queryset, "override_enable_sms", "enabled")

    def set_sms_override_disabled(self, request, queryset):
        return self._bulk_set_override(request, queryset, "override_enable_sms", "disabled")

    def set_sms_override_inherit(self, request, queryset):
        return self._bulk_set_override(request, queryset, "override_enable_sms", "inherit")

    set_email_override_enabled.short_description = "Set Email override = enabled for selected schedules"
    set_email_override_disabled.short_description = "Set Email override = disabled for selected schedules"
    set_email_override_inherit.short_description = "Set Email override = inherit (use ChannelSettings)"
    set_sms_override_enabled.short_description = "Set SMS override = enabled for selected schedules"
    set_sms_override_disabled.short_description = "Set SMS override = disabled for selected schedules"
    set_sms_override_inherit.short_description = "Set SMS override = inherit (use ChannelSettings)"

    actions = (
        "export_schedule_xlsx",
        "export_schedule_pdf",
        "trigger_alert_scan",
        "set_email_override_enabled",
        "set_email_override_disabled",
        "set_email_override_inherit",
        "set_sms_override_enabled",
        "set_sms_override_disabled",
        "set_sms_override_inherit",
    )

    def trigger_alert_scan(self, request, queryset):
        """Admin action to enqueue the alert scan task (checks upcoming
        program instances and creates alerts)."""
        try:
            from .tasks import check_alerts_task

            check_alerts_task.apply_async()
            self.message_user(request, "اسکن هشدارها در صف قرار گرفت (Celery)")
        except Exception as e:
            self.message_user(request, f"خطا در قرار دادن اسکن در صف: {e}", level="error")

    actions = (
        "export_schedule_xlsx",
        "export_schedule_pdf",
        "trigger_alert_scan",
    )

    def export_schedule_xlsx(self, request, queryset):
        """Export selected schedule (one) to a downloadable XLSX file."""
        if openpyxl is None:
            self.message_user(request, "openpyxl is not installed; cannot export XLSX", level="error")
            return
        if queryset.count() != 1:
            self.message_user(request, "لطفا تنها یک برنامه را انتخاب کنید تا خروجی اکسل تولید شود.")
            return
        schedule = queryset.first()
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Schedule"

        # Header
        ws["A1"] = "شبکه"
        ws["B1"] = schedule.channel.name
        ws["A2"] = "تاریخ"
        ws["B2"] = str(schedule.schedule_date)

        # Table headers
        headers = ["ردیف", "عنوان برنامه", "شروع", "پایان", "مدت", "وضعیت", "منبع", "نوع پخش", "یادداشت"]
        for i, h in enumerate(headers, start=1):
            ws.cell(row=4, column=i, value=h)

        rows = Schedule.objects.filter(channel=schedule.channel, schedule_date=schedule.schedule_date).order_by("order")
        for idx, row in enumerate(rows, start=1):
            pi = row.program_instance
            start = pi.scheduled_start.strftime("%H:%M:%S")
            end = pi.scheduled_end.strftime("%H:%M:%S")
            duration = int((pi.scheduled_end - pi.scheduled_start).total_seconds() / 60)
            values = [
                idx,
                pi.program.title,
                start,
                end,
                f"{duration} دقیقه",
                pi.status,
                pi.program.media_source,
                pi.program.broadcast_type,
                row.notes,
            ]
            for c_idx, v in enumerate(values, start=1):
                ws.cell(row=4 + idx, column=c_idx, value=v)

        # Auto-width
        for column_cells in ws.columns:
            length = max((len(str(cell.value)) for cell in column_cells if cell.value), default=0)
            ws.column_dimensions[get_column_letter(column_cells[0].column)].width = min(50, length + 2)

        bio = io.BytesIO()
        wb.save(bio)
        bio.seek(0)
        filename = f"schedule-{schedule.channel.code}-{schedule.schedule_date}.xlsx"
        response = HttpResponse(
            bio.read(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

    def export_schedule_pdf(self, request, queryset):
        """Export selected schedule to PDF using WeasyPrint (if available)."""
        # Import WeasyPrint lazily to avoid printing diagnostic messages
        # during test discovery or when the admin module is imported.
        from .weasyprint_helper import HTML

        if HTML is None:
            self.message_user(request, "WeasyPrint is not installed or missing native deps; cannot generate PDF", level="error")
            return
        if queryset.count() != 1:
            self.message_user(request, "لطفا تنها یک برنامه را انتخاب کنید تا خروجی PDF تولید شود.")
            return
        schedule = queryset.first()
        # Prepare context
        rows = Schedule.objects.filter(channel=schedule.channel, schedule_date=schedule.schedule_date).order_by("order")
        context = {
            "schedule": schedule,
            "rows": rows,
        }
        html = render_to_string("programs/schedule_pdf.html", context)
        pdf = HTML(string=html).write_pdf()
        filename = f"schedule-{schedule.channel.code}-{schedule.schedule_date}.pdf"
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


@admin.register(Conductor)
class ConductorAdmin(admin.ModelAdmin):
    list_display = ("schedule", "priority", "auto_record", "is_active")
    search_fields = ("schedule__program_instance__program__title",)
    list_filter = ("priority", "is_active", "auto_record", "auto_play_intro")
    readonly_fields = ("created_at", "updated_at")


@admin.register(ConductorLog)
class ConductorLogAdmin(admin.ModelAdmin):
    list_display = ("conductor", "action", "status", "timestamp")
    search_fields = ("conductor__schedule__program_instance__program__title", "message")
    list_filter = ("action", "status", "timestamp")
    readonly_fields = ("timestamp", "conductor", "action", "status", "message")


# ============================================================================
# آنالیتیکس
# ============================================================================


@admin.register(AnalyticsData)
class AnalyticsDataAdmin(admin.ModelAdmin):
    @admin.register(LiveSegment)
    class LiveSegmentAdmin(admin.ModelAdmin):
        list_display = ("program_instance", "title", "start_offset", "duration", "approved")
        search_fields = ("program_instance__program__title", "title")

    @admin.register(ScheduleTemplate)
    class ScheduleTemplateAdmin(admin.ModelAdmin):
        list_display = ("name", "channel", "day_of_week", "start_time", "duration", "is_active")
        search_fields = ("name", "channel__name")

    @admin.register(Evaluation)
    class EvaluationAdmin(admin.ModelAdmin):
        list_display = ("target", "evaluator", "status", "created_at", "evaluated_at")
        search_fields = ("evaluator__full_name",)
        readonly_fields = ("created_at", "evaluated_at")

    @admin.register(Alert)
    class AlertAdmin(admin.ModelAdmin):
        list_display = ("trigger", "schedule", "method", "sent", "created_at")
        search_fields = ("schedule__program_instance__program__title", "message")
        actions = ("send_alerts_via_email",)

        def send_alerts_via_email(self, request, queryset):
            """Admin action to enqueue selected alerts to be sent via email."""
            sent = 0
            enqueued = 0
            for alert in queryset:
                if alert.method != "email":
                    continue
                if alert.sent:
                    sent += 1
                    continue
                try:
                    from .tasks import send_alert_email

                    send_alert_email.apply_async(args=[alert.id])
                    enqueued += 1
                except Exception as e:
                    self.message_user(request, f"خطا در قرار دادن هشدار در صف: {e}", level="error")
            self.message_user(request, f"هشدارهای در صف: {enqueued}، قبلاً ارسال‌شده: {sent}")

    @admin.register(ReplacementRule)
    class ReplacementRuleAdmin(admin.ModelAdmin):
        list_display = ("schedule", "priority")
        filter_horizontal = ("candidates",)


@admin.register(RecipientMapping)
class RecipientMappingAdmin(admin.ModelAdmin):
    list_display = ("role", "active", "emails_preview")
    filter_horizontal = ("persons",)
    search_fields = ("role__name", "role__code")

    class RecipientMappingForm(forms.ModelForm):
        emails_list = forms.CharField(
            required=False,
            label="ایمیل‌های مستقیم (با ویرگول جدا کنید)",
            help_text="لیستی از آدرس‌های ایمیل جداشده با ویرگول",
            widget=forms.Textarea(attrs={"rows": 2}),
        )

        class Meta:
            model = None  # set dynamically in __init__ below
            fields = ("role", "persons", "active", "emails_list")

        def __init__(self, *args, **kwargs):
            # Model is set by admin when constructing the form class
            super().__init__(*args, **kwargs)
            if self.instance and getattr(self.instance, "emails", None):
                self.fields["emails_list"].initial = ", ".join(self.instance.emails)

        def clean_emails_list(self):
            raw = self.cleaned_data.get("emails_list", "") or ""
            parts = [p.strip() for p in raw.split(",") if p.strip()]
            # validate each
            for e in parts:
                try:
                    validate_email(e)
                except ValidationError as err:
                    raise ValidationError(f"آدرس ایمیل نامعتبر: {e}") from err
            return parts

        def save(self, commit=True):
            instance = super().save(commit=False)
            instance.emails = self.cleaned_data.get("emails_list") or []
            if commit:
                instance.save()
                self.save_m2m()
            return instance

    def get_form(self, request, obj=None, **kwargs):
        # bind the Meta.model dynamically so ModelForm works
        form = type("_RMForm", (self.RecipientMappingForm,), {})
        form.Meta.model = self.model
        return form

    def emails_preview(self, obj):
        if not obj or not obj.emails:
            return ""
        return ", ".join(obj.emails[:3]) + ("..." if len(obj.emails) > 3 else "")

    emails_preview.short_description = "ایمیل‌ها"


@admin.register(ChannelSettings)
class ChannelSettingsAdmin(admin.ModelAdmin):
    list_display = ("enable_email", "enable_sms", "default_from_email", "default_from_number", "updated_at")
    readonly_fields = ("updated_at",)
    fieldsets = (
        (None, {"fields": ("enable_email", "enable_sms")}),
        ("Senders", {"fields": ("default_from_email", "default_from_number", "updated_at")}),
    )
    actions = ("run_e2e_test",)
    change_form_template = "admin/programs/channelsettings/change_form.html"

    def run_e2e_test(self, request, queryset):
        """Admin action to trigger E2E test(s) for the selected ChannelSettings rows.

        This runs the management command `send_test_alert` (creates sample data) and
        records output to `E2ERun` model.
        """
        from django.core.management import call_command
        from io import StringIO
        from django.utils import timezone
        import json

        created = 0
        for _cs in queryset:
            # default to both methods for quick validation
            for method in ("email", "sms"):
                sio = StringIO()
                try:
                    call_command("send_test_alert", "--create", f"--method={method}", stdout=sio)
                    out = sio.getvalue()
                    # try to parse E2E_RESULT JSON line
                    parsed = None
                    for line in out.splitlines():
                        if line.startswith("E2E_RESULT:"):
                            try:
                                parsed = json.loads(line.split("E2E_RESULT:", 1)[1].strip())
                            except Exception:
                                parsed = None
                    if parsed is not None:
                        success = bool(parsed.get("ok"))
                        output = json.dumps(parsed, ensure_ascii=False)
                    else:
                        success = False
                        output = out
                except Exception as exc:  # pragma: no cover - external
                    out = str(exc)
                    success = False
                    output = out

                E2ERun.objects.create(method=method, success=success, output=output, finished_at=timezone.now())
                created += 1

        self.message_user(request, f"E2E runs recorded: {created}")

    run_e2e_test.short_description = "اجرای تست E2E (Email+SMS) و ثبت خروجی"

    # add a custom view to run E2E for a single object via a button on the change form
    def get_urls(self):
        from django.urls import path

        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:pk>/run-e2e/",
                self.admin_site.admin_view(self.run_e2e_view),
                name="programs_channelsettings_run_e2e",
            ),
        ]
        return custom_urls + urls

    def run_e2e_view(self, request, pk, *args, **kwargs):
        from django.shortcuts import redirect, get_object_or_404
        from django.core.management import call_command
        from io import StringIO
        from django.utils import timezone
        import json

        obj = get_object_or_404(ChannelSettings, pk=pk)
        sio = StringIO()
        created = 0
        for method in ("email", "sms"):
            try:
                call_command("send_test_alert", "--create", f"--method={method}", stdout=sio)
                out = sio.getvalue()
                parsed = None
                for line in out.splitlines():
                    if line.startswith("E2E_RESULT:"):
                        try:
                            parsed = json.loads(line.split("E2E_RESULT:", 1)[1].strip())
                        except Exception:
                            parsed = None
                if parsed is not None:
                    success = bool(parsed.get("ok"))
                    output = json.dumps(parsed, ensure_ascii=False)
                else:
                    success = False
                    output = out
            except Exception as exc:  # pragma: no cover - external
                output = str(exc)
                success = False

            E2ERun.objects.create(method=method, success=success, output=output, finished_at=timezone.now())
            created += 1

        self.message_user(request, f"E2E runs recorded: {created}")
        return redirect(request.META.get("HTTP_REFERER", f"../{pk}/change/"))

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        extra_context = extra_context or {}
        extra_context["show_run_e2e"] = True
        return super().changeform_view(request, object_id, form_url, extra_context=extra_context)


@admin.register(E2ERun)
class E2ERunAdmin(admin.ModelAdmin):
    list_display = ("method", "started_at", "finished_at", "success")
    readonly_fields = ("method", "started_at", "finished_at", "success", "pretty_output")
    search_fields = ("method",)
    ordering = ("-started_at",)

    def pretty_output(self, obj):
        from django.utils.html import format_html
        import json

        if not obj.output:
            return ""
        try:
            parsed = json.loads(obj.output)
            pretty = json.dumps(parsed, ensure_ascii=False, indent=2)
        except Exception:
            pretty = obj.output
        return format_html('<pre style="white-space: pre-wrap;">{}</pre>', pretty)

    pretty_output.short_description = "خروجی"
