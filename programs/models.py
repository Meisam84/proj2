from datetime import timedelta

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

# ============================================================================
# بخش 1: اطلاعات پایه و جداول مرجع (اتوماتیک پر می‌شود)
# ============================================================================


class Channel(models.Model):
    """شبکه‌ها و ایستگاه‌های پخش"""

    name = models.CharField(max_length=100, verbose_name="نام شبکه", unique=True)
    code = models.CharField(max_length=20, verbose_name="کد شبکه", unique=True)
    program_type = models.CharField(
        max_length=10, choices=[("radio", "رادیو"), ("tv", "تلویزیون")], verbose_name="نوع پخش"
    )
    description = models.TextField(verbose_name="توضیحات", blank=True)
    # Geo & timezone (useful for prayer times and localization)
    latitude = models.FloatField(verbose_name="عرض جغرافیایی", null=True, blank=True)
    longitude = models.FloatField(verbose_name="طول جغرافیایی", null=True, blank=True)
    timezone = models.CharField(max_length=64, verbose_name="منطقهٔ زمانی", blank=True)
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت")

    class Meta:
        verbose_name = "شبکه"
        verbose_name_plural = "شبکه‌ها"

    def __str__(self):
        return self.name


class Genre(models.Model):
    """ژانرهای برنامه‌ها"""

    name = models.CharField(max_length=100, verbose_name="نام ژانر", unique=True)
    code = models.CharField(max_length=20, verbose_name="کد ژانر", unique=True)
    description = models.TextField(verbose_name="توضیحات", blank=True)

    class Meta:
        verbose_name = "ژانر"
        verbose_name_plural = "ژانرها"

    def __str__(self):
        return self.name


class Role(models.Model):
    """نقش‌های افراد (تهیه‌کننده، مجری، کارگردان، ...)"""

    name = models.CharField(max_length=100, verbose_name="نام نقش", unique=True)
    code = models.CharField(max_length=20, verbose_name="کد نقش", unique=True)
    description = models.TextField(verbose_name="توضیحات", blank=True)

    class Meta:
        verbose_name = "نقش"
        verbose_name_plural = "نقش‌ها"

    def __str__(self):
        return self.name


class Person(models.Model):
    """افراد (تهیه‌کننده، مجری، کارگردان، نویسنده، ...)"""

    full_name = models.CharField(max_length=150, verbose_name="نام کامل")
    email = models.EmailField(verbose_name="ایمیل", blank=True)
    phone = models.CharField(max_length=20, verbose_name="تلفن", blank=True)
    bio = models.TextField(verbose_name="بیوگرافی", blank=True)
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت")

    class Meta:
        verbose_name = "فرد"
        verbose_name_plural = "افراد"

    def __str__(self):
        return self.full_name


class TargetAudience(models.Model):
    """مخاطب هدف برنامه"""

    name = models.CharField(max_length=100, verbose_name="نام دسته‌بندی", unique=True)
    age_min = models.IntegerField(verbose_name="حداقل سن", validators=[MinValueValidator(0), MaxValueValidator(150)])
    age_max = models.IntegerField(verbose_name="حداکثر سن", validators=[MinValueValidator(0), MaxValueValidator(150)])
    description = models.TextField(verbose_name="توضیحات", blank=True)

    class Meta:
        verbose_name = "مخاطب هدف"
        verbose_name_plural = "مخاطبین هدف"

    def __str__(self):
        return f"{self.name} ({self.age_min}-{self.age_max})"


# ============================================================================
# بخش 2: اطلاعات اساسی برنامه (ورود اولیه)
# ============================================================================


class Program(models.Model):
    """برنامه اصلی - اطلاعات ثابت و پایه‌ای"""

    title = models.CharField(max_length=200, verbose_name="عنوان برنامه")
    subtitle = models.CharField(max_length=300, verbose_name="زیرعنوان", blank=True)
    description = models.TextField(verbose_name="توضیحات اصلی")
    channel = models.ForeignKey(Channel, on_delete=models.PROTECT, verbose_name="شبکه")
    genres = models.ManyToManyField(Genre, verbose_name="ژانرها")
    target_audiences = models.ManyToManyField(TargetAudience, verbose_name="مخاطبین هدف")

    # مدت زمان معمولی برنامه (پشتیبانی دقیق hh:mm:ss)
    default_duration = models.DurationField(default=timedelta(minutes=60), verbose_name="مدت زمان معمولی")

    # حالت‌های پخش و منبع
    BROADCAST_TYPE_CHOICES = [
        ("relay", "رله"),
        ("live", "زنده"),
        ("supply", "تأمینی"),
        ("recorded", "ضبطی"),
        ("repeat", "تکرار"),
    ]
    broadcast_type = models.CharField(
        max_length=20, choices=BROADCAST_TYPE_CHOICES, default="recorded", verbose_name="نوع پخش"
    )

    PROGRAM_ORIGIN_CHOICES = [
        ("produced", "تولیدی"),
        ("live", "زنده"),
        ("supply", "تأمینی"),
    ]
    program_origin = models.CharField(
        max_length=20, choices=PROGRAM_ORIGIN_CHOICES, default="produced", verbose_name="نوع برنامه"
    )

    MEDIA_SOURCE_CHOICES = [
        ("automation", "اتوماسیون"),
        ("studio", "استودیو پخش"),
        ("relay", "رله شبکه"),
        ("supply_folder", "پوشه تأمین"),
    ]
    media_source = models.CharField(
        max_length=30, choices=MEDIA_SOURCE_CHOICES, default="automation", verbose_name="محل پخش"
    )

    # وضعیت برنامه
    is_live = models.BooleanField(default=False, verbose_name="برنامه زنده")
    is_repeatable = models.BooleanField(default=False, verbose_name="قابل تکرار")
    is_active = models.BooleanField(default=True, verbose_name="فعال")

    # فراداده
    language = models.CharField(max_length=10, default="fa", verbose_name="زبان")
    keywords = models.CharField(max_length=500, verbose_name="کلمات کلیدی", blank=True)

    # ارزیابی و تنظیمات پیش‌فرض
    evaluation_required = models.BooleanField(default=True, verbose_name="نیازمند ارزیابی")
    EVALUATION_STATUS = [
        ("pending", "در انتظار"),
        ("approved", "تأیید‌شده"),
        ("rejected", "رد شده"),
    ]
    evaluation_status = models.CharField(
        max_length=20, choices=EVALUATION_STATUS, default="pending", verbose_name="وضعیت ارزیابی"
    )

    # برنامه‌هایی که باید سر ساعت ثابت بمانند
    fixed_on_clock = models.BooleanField(default=False, verbose_name="قفل سر ساعت")

    # نصب و متادیتای گسترش‌پذیر
    metadata = models.JSONField(default=dict, blank=True, verbose_name="متادیتا")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخرین بروزرسانی")

    class Meta:
        verbose_name = "برنامه"
        verbose_name_plural = "برنامه‌ها"

    def __str__(self):
        return self.title


class ProgramMember(models.Model):
    """اعضای برنامه (تهیه‌کننده، مجری، کارگردان، ...)"""

    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name="members", verbose_name="برنامه")
    person = models.ForeignKey(Person, on_delete=models.CASCADE, verbose_name="فرد")
    role = models.ForeignKey(Role, on_delete=models.PROTECT, verbose_name="نقش")
    is_primary = models.BooleanField(default=False, verbose_name="نقش اصلی")

    class Meta:
        verbose_name = "عضو برنامه"
        verbose_name_plural = "اعضای برنامه"
        unique_together = ("program", "person", "role")

    def __str__(self):
        return f"{self.program.title} - {self.person.full_name} ({self.role.name})"


# ============================================================================
# بخش 3: نمونه‌های برنامه و ورود اطلاعات برای هر پخش
# ============================================================================


class ProgramInstance(models.Model):
    """نمونه‌های برنامه برای هر پخش (زمان‌بندی)"""

    STATUS_CHOICES = [
        ("draft", "مسودهٔ"),
        ("pending", "در انتظار تایید"),
        ("approved", "تایید‌شده"),
        ("scheduled", "زمان‌بندی‌شده"),
        ("broadcasting", "در حال پخش"),
        ("completed", "تکمیل‌شده"),
        ("cancelled", "لغو‌شده"),
    ]

    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name="instances", verbose_name="برنامه")
    episode_number = models.IntegerField(verbose_name="شماره قسمت", blank=True, null=True)
    episode_title = models.CharField(max_length=200, verbose_name="عنوان قسمت", blank=True)
    episode_description = models.TextField(verbose_name="توضیحات قسمت", blank=True)

    scheduled_start = models.DateTimeField(verbose_name="زمان شروع برنامه‌ریزی‌شده")
    scheduled_end = models.DateTimeField(verbose_name="زمان پایان برنامه‌ریزی‌شده")
    # اطلاعات ارسال/تأیید
    source_folder = models.CharField(max_length=200, blank=True, verbose_name="پوشه تأمین")
    submitted_at = models.DateTimeField(blank=True, null=True, verbose_name="زمان ارسال")
    submitted_by = models.CharField(max_length=150, blank=True, verbose_name="ارسال‌شده توسط")
    approved_at = models.DateTimeField(blank=True, null=True, verbose_name="زمان تأیید")
    approved_by = models.CharField(max_length=150, blank=True, verbose_name="تایید‌شده توسط")

    actual_start = models.DateTimeField(verbose_name="زمان شروع واقعی", blank=True, null=True)
    actual_end = models.DateTimeField(verbose_name="زمان پایان واقعی", blank=True, null=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft", verbose_name="وضعیت")
    notes = models.TextField(verbose_name="یادداشت‌ها", blank=True)

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخرین بروزرسانی")

    class Meta:
        verbose_name = "نمونه برنامه"
        verbose_name_plural = "نمونه‌های برنامه"
        ordering = ["-scheduled_start"]

    def __str__(self):
        return f"{self.program.title} - {self.scheduled_start.strftime('%Y-%m-%d %H:%M')}"

    def get_duration(self):
        """محاسبه مدت زمان"""
        return (self.scheduled_end - self.scheduled_start).total_seconds() / 60


class ProgramGuest(models.Model):
    """مهمانان برنامه"""

    program_instance = models.ForeignKey(
        ProgramInstance, on_delete=models.CASCADE, related_name="guests", verbose_name="نمونه برنامه"
    )
    person = models.ForeignKey(Person, on_delete=models.CASCADE, verbose_name="فرد")
    guest_order = models.IntegerField(default=0, verbose_name="ترتیب ظهور")

    class Meta:
        verbose_name = "مهمان برنامه"
        verbose_name_plural = "مهمانان برنامه"
        unique_together = ("program_instance", "person")

    def __str__(self):
        return f"{self.program_instance.program.title} - {self.person.full_name}"


class LiveSegment(models.Model):
    """آیتم‌ها/بلاک‌ها برای برنامه‌های زنده؛ برای ارزیابی دقیق زمان‌بندی"""

    program_instance = models.ForeignKey(
        ProgramInstance, on_delete=models.CASCADE, related_name="live_segments", verbose_name="نمونه برنامه"
    )
    title = models.CharField(max_length=200, verbose_name="عنوان آیتم")
    start_offset = models.DurationField(verbose_name="افست شروع")
    duration = models.DurationField(verbose_name="مدت زمان")
    approved = models.BooleanField(default=False, verbose_name="تایید شده")
    notes = models.TextField(blank=True, verbose_name="یادداشت")

    class Meta:
        verbose_name = "آیتم زنده"
        verbose_name_plural = "آیتم‌های زنده"

    def __str__(self):
        return f"{self.program_instance} - {self.title}"


class ProgramAsset(models.Model):
    """فایل‌های صوتی/تصویری و منابع برنامه"""

    ASSET_TYPE_CHOICES = [
        ("intro", "اپنینگ"),
        ("outro", "انگلیزی"),
        ("audio", "فایل صوتی"),
        ("video", "فایل تصویری"),
        ("subtitle", "زیرنویس"),
        ("thumbnail", "تصویر بند انگشتی"),
        ("document", "سند"),
        ("other", "سایر"),
    ]

    program_instance = models.ForeignKey(
        ProgramInstance, on_delete=models.CASCADE, related_name="assets", verbose_name="نمونه برنامه"
    )
    asset_type = models.CharField(max_length=20, choices=ASSET_TYPE_CHOICES, verbose_name="نوع منبع")
    file = models.FileField(upload_to="programs/assets/%Y/%m/%d/", verbose_name="فایل")
    title = models.CharField(max_length=200, verbose_name="عنوان منبع")
    description = models.TextField(verbose_name="توضیحات", blank=True)
    duration = models.IntegerField(verbose_name="مدت زمان (ثانیه)", blank=True, null=True)
    file_size = models.BigIntegerField(verbose_name="حجم فایل (بایت)", blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ آپلود")

    class Meta:
        verbose_name = "منبع برنامه"
        verbose_name_plural = "منابع برنامه"

    def __str__(self):
        return f"{self.program_instance.program.title} - {self.get_asset_type_display()}"


# ============================================================================
# بخش 4: ویرایش، مسودات و نسخه‌ها
# ============================================================================


class ProgramVersion(models.Model):
    """نسخه‌های مختلف برنامه و تاریخچه تغییرات"""

    program_instance = models.ForeignKey(
        ProgramInstance, on_delete=models.CASCADE, related_name="versions", verbose_name="نمونه برنامه"
    )
    version_number = models.IntegerField(verbose_name="شماره نسخه")
    description = models.TextField(verbose_name="توضیحات تغییرات", blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    created_by = models.CharField(max_length=100, verbose_name="ایجاد‌شده توسط")

    class Meta:
        verbose_name = "نسخهٔ برنامه"
        verbose_name_plural = "نسخه‌های برنامه"
        unique_together = ("program_instance", "version_number")

    def __str__(self):
        return f"{self.program_instance.program.title} - v{self.version_number}"


class ScheduleModification(models.Model):
    """تعدیلات برنامه‌ریزی"""

    program_instance = models.ForeignKey(
        ProgramInstance, on_delete=models.CASCADE, related_name="modifications", verbose_name="نمونه برنامه"
    )
    modification_type = models.CharField(
        max_length=20,
        choices=[
            ("time_change", "تغییر زمان"),
            ("cancellation", "لغو"),
            ("postponement", "تعویق"),
            ("replacement", "جایگزینی"),
        ],
        verbose_name="نوع تعدیل",
    )
    reason = models.TextField(verbose_name="دلیل")
    old_start_time = models.DateTimeField(verbose_name="زمان شروع قبلی", blank=True, null=True)
    old_end_time = models.DateTimeField(verbose_name="زمان پایان قبلی", blank=True, null=True)
    new_start_time = models.DateTimeField(verbose_name="زمان شروع جدید", blank=True, null=True)
    new_end_time = models.DateTimeField(verbose_name="زمان پایان جدید", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ تعدیل")
    created_by = models.CharField(max_length=100, verbose_name="ایجاد‌شده توسط")

    class Meta:
        verbose_name = "تعدیل برنامه‌ریزی"
        verbose_name_plural = "تعدیلات برنامه‌ریزی"

    def __str__(self):
        return f"{self.program_instance.program.title} - {self.get_modification_type_display()}"


# ============================================================================
# بخش 5: مدیریت و کنترل (کنداکتور)
# ============================================================================


class Schedule(models.Model):
    """برنامه‌ریزی نهایی برای کنداکتور"""

    channel = models.ForeignKey(Channel, on_delete=models.PROTECT, verbose_name="شبکه")
    schedule_date = models.DateField(verbose_name="تاریخ برنامه‌ریزی")
    program_instance = models.OneToOneField(
        ProgramInstance, on_delete=models.CASCADE, related_name="schedule", verbose_name="نمونه برنامه"
    )
    order = models.IntegerField(verbose_name="ترتیب پخش در روز")
    # قابلیت‌ها برای مدیریت نسخه‌ها و قفل برنامه‌ها
    locked = models.BooleanField(default=False, verbose_name="قفل شده")
    initial_version = models.BooleanField(default=False, verbose_name="نسخه اولیه")
    updated_version = models.BooleanField(default=False, verbose_name="نسخه بروز")
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    notes = models.TextField(verbose_name="یادداشت‌های کنداکتور", blank=True)

    # Per-schedule overrides for delivery channels. Use a tri-state choice so
    # administrators can explicitly enable/disable a channel for this schedule
    # or leave it to inherit the global `ChannelSettings` value.
    OVERRIDE_CHOICES = [
        ("inherit", "وراثت (استفاده از تنظیمات سراسری)"),
        ("enabled", "فعال"),
        ("disabled", "غیرفعال"),
    ]

    override_enable_email = models.CharField(
        max_length=10,
        choices=OVERRIDE_CHOICES,
        default="inherit",
        verbose_name="بازنویسی: ایمیل",
        help_text="سه‌حالته: وراثت -> استفاده از تنظیمات سراسری؛ فعال -> ارسال ایمیل اجباری؛ غیرفعال -> جلوگیری از ارسال ایمیل برای این برنامه‌ریزی.",
    )
    override_enable_sms = models.CharField(
        max_length=10,
        choices=OVERRIDE_CHOICES,
        default="inherit",
        verbose_name="بازنویسی: پیامک",
        help_text="سه‌حالته: وراثت -> استفاده از تنظیمات سراسری؛ فعال -> ارسال پیامک اجباری؛ غیرفعال -> جلوگیری از ارسال پیامک برای این برنامه‌ریزی.",
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخرین بروزرسانی")

    class Meta:
        verbose_name = "برنامه‌ریزی"
        verbose_name_plural = "برنامه‌ریزی‌ها"
        ordering = ["schedule_date", "order"]
        unique_together = ("channel", "schedule_date", "order")

    def __str__(self):
        return f"{self.channel.name} - {self.schedule_date} - {self.program_instance.program.title}"

    def email_enabled(self):
        """Resolve whether email should be used for this schedule.

        Precedence: schedule override -> ChannelSettings -> sensible default (True).
        """
        if self.override_enable_email == "enabled":
            return True
        if self.override_enable_email == "disabled":
            return False
        # inherit
        try:
            cs = ChannelSettings.objects.first()
        except Exception:
            cs = None
        if cs is None:
            return True
        return bool(cs.enable_email)

    def sms_enabled(self):
        """Resolve whether SMS should be used for this schedule.

        Precedence: schedule override -> ChannelSettings -> sensible default (False).
        """
        if self.override_enable_sms == "enabled":
            return True
        if self.override_enable_sms == "disabled":
            return False
        # inherit
        try:
            cs = ChannelSettings.objects.first()
        except Exception:
            cs = None
        if cs is None:
            # fall back to previous behavior where absence of ChannelSettings
            # did not block SMS sending (maintain backward compatibility
            # for existing tests and deployments)
            return True
        return bool(cs.enable_sms)


class Conductor(models.Model):
    """کنداکتور - دستورالعمل‌های اتوماتیک برای هر برنامه"""

    PRIORITY_CHOICES = [
        (1, "خیلی کم"),
        (2, "کم"),
        (3, "متوسط"),
        (4, "زیاد"),
        (5, "خیلی زیاد"),
    ]

    schedule = models.OneToOneField(
        Schedule, on_delete=models.CASCADE, related_name="conductor", verbose_name="برنامه‌ریزی"
    )

    # دستورالعمل‌های اتوماتیک
    auto_play_intro = models.BooleanField(default=True, verbose_name="پخش خودکار اپنینگ")
    auto_play_outro = models.BooleanField(default=True, verbose_name="پخش خودکار انگلیزی")
    auto_adjust_volume = models.BooleanField(default=False, verbose_name="تنظیم خودکار صدا")
    auto_record = models.BooleanField(default=True, verbose_name="ضبط خودکار")

    # اولویت و ترتیب
    priority = models.IntegerField(choices=PRIORITY_CHOICES, default=3, verbose_name="اولویت")
    backup_program = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, verbose_name="برنامه جایگزین"
    )

    # قواعد جایگزینی: انعطاف‌پذیر و قابل تنظیم
    replacement_policy = models.JSONField(default=dict, blank=True, verbose_name="قوانین جایگزینی")

    # دستورالعمل‌های خاص
    special_instructions = models.TextField(verbose_name="دستورالعمل‌های خاص", blank=True)
    contact_person = models.ForeignKey(
        Person, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="شخص تماس"
    )

    # وضعیت
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخرین بروزرسانی")

    class Meta:
        verbose_name = "کنداکتور"
        verbose_name_plural = "کنداکتورها"

    def __str__(self):
        return f"کنداکتور - {self.schedule.program_instance.program.title}"


class ConductorLog(models.Model):
    """ثبت اجرای دستورالعمل‌های کنداکتور"""

    ACTION_CHOICES = [
        ("start", "شروع"),
        ("play_intro", "پخش اپنینگ"),
        ("play_program", "پخش برنامه"),
        ("play_outro", "پخش انگلیزی"),
        ("pause", "توقف"),
        ("resume", "ادامه"),
        ("stop", "پایان"),
        ("error", "خطا"),
        ("manual_intervention", "مداخلهٔ دستی"),
    ]

    conductor = models.ForeignKey(Conductor, on_delete=models.CASCADE, related_name="logs", verbose_name="کنداکتور")
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, verbose_name="اقدام")
    status = models.CharField(
        max_length=20,
        choices=[
            ("success", "موفق"),
            ("failed", "ناموفق"),
            ("warning", "هشدار"),
        ],
        verbose_name="وضعیت",
    )
    message = models.TextField(verbose_name="پیام")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="زمان")

    class Meta:
        verbose_name = "ثبت کنداکتور"
        verbose_name_plural = "ثبت‌های کنداکتور"
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.conductor.schedule.program_instance.program.title} - {self.action}"


class AnalyticsData(models.Model):
    """داده‌های تحلیلی برای هر برنامه"""

    program_instance = models.OneToOneField(
        ProgramInstance, on_delete=models.CASCADE, related_name="analytics", verbose_name="نمونه برنامه"
    )
    total_viewers = models.IntegerField(default=0, verbose_name="تعداد کل بینندگان")
    average_rating = models.FloatField(
        default=0.0, validators=[MinValueValidator(0), MaxValueValidator(10)], verbose_name="امتیاز متوسط"
    )
    comments_count = models.IntegerField(default=0, verbose_name="تعداد نظرات")
    social_mentions = models.IntegerField(default=0, verbose_name="ذکر در شبکه‌های اجتماعی")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخرین بروزرسانی")

    class Meta:
        verbose_name = "داده‌های تحلیلی"
        verbose_name_plural = "داده‌های تحلیلی"

    def __str__(self):
        return f"تحلیل - {self.program_instance.program.title}"


class ScheduleTemplate(models.Model):
    """قالب کنداکتور هفتگی (weekly template)"""

    channel = models.ForeignKey(Channel, on_delete=models.PROTECT, verbose_name="شبکه")
    name = models.CharField(max_length=150, verbose_name="نام قالب")
    day_of_week = models.IntegerField(verbose_name="روز هفته")
    start_time = models.TimeField(verbose_name="زمان شروع")
    duration = models.DurationField(verbose_name="مدت زمان")
    order = models.IntegerField(verbose_name="ترتیب")
    is_locked = models.BooleanField(default=False, verbose_name="قفل قالب")
    is_active = models.BooleanField(default=True, verbose_name="فعال")

    class Meta:
        verbose_name = "قالب برنامه‌ریزی"
        verbose_name_plural = "قالب‌های برنامه‌ریزی"

    def __str__(self):
        return f"{self.channel} - {self.name} ({self.day_of_week})"


class Evaluation(models.Model):
    """ثبت ارزیابی برای ProgramInstance یا Playlist entry (generic)"""

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    target = GenericForeignKey("content_type", "object_id")

    evaluator = models.ForeignKey("Person", on_delete=models.SET_NULL, null=True, blank=True, verbose_name="ارزیاب")
    status = models.CharField(
        max_length=20,
        choices=[("pending", "در انتظار"), ("approved", "تایید"), ("rejected", "رد")],
        default="pending",
        verbose_name="وضعیت",
    )
    comment = models.TextField(blank=True, verbose_name="توضیحات")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان ثبت")
    evaluated_at = models.DateTimeField(blank=True, null=True, verbose_name="زمان ارزیابی")

    class Meta:
        verbose_name = "ارزیابی"
        verbose_name_plural = "ارزیابی‌ها"

    def __str__(self):
        return f"ارزیابی - {self.content_type}#{self.object_id} - {self.status}"


class Alert(models.Model):
    """اعلان‌ها و هشدارها برای کاربران/نقش‌ها"""

    TRIGGER_CHOICES = [
        ("not_approved_1h", "یک ساعت قبل - تایید نشده"),
        ("manual_change", "تغییر دستی"),
        ("replacement_used", "جایگزینی استفاده شد"),
    ]
    trigger = models.CharField(max_length=50, choices=TRIGGER_CHOICES, verbose_name="محل تریگر")
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, related_name="alerts", verbose_name="برنامه‌ریزی")
    recipient_roles = models.JSONField(default=list, blank=True, verbose_name="نقش‌های دریافتی")
    message = models.TextField(verbose_name="متن پیام")
    method = models.CharField(
        max_length=20,
        choices=[("ui", "UI"), ("sound", "صدا"), ("email", "ایمیل")],
        default="ui",
        verbose_name="روش اعلان",
    )
    sent = models.BooleanField(default=False, verbose_name="ارسال شده")
    sent_at = models.DateTimeField(blank=True, null=True, verbose_name="زمان ارسال")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان ایجاد")

    class Meta:
        verbose_name = "هشدار"
        verbose_name_plural = "هشدارها"

    def __str__(self):
        return f"هشدار - {self.get_trigger_display()} - {self.schedule}"


class ReplacementRule(models.Model):
    """قوانین انتخاب برنامه جایگزین برای یک Schedule entry"""

    schedule = models.ForeignKey(
        Schedule, on_delete=models.CASCADE, related_name="replacement_rules", verbose_name="برنامه‌ریزی"
    )
    candidates = models.ManyToManyField(Program, verbose_name="نامزدهای جایگزینی")
    priority = models.IntegerField(default=50, verbose_name="اولویت")

    class Meta:
        verbose_name = "قانون جایگزینی"
        verbose_name_plural = "قوانین جایگزینی"

    def __str__(self):
        return f"قانون جایگزینی ({self.schedule})"


class RecipientMapping(models.Model):
    """Map a role code to specific persons and/or direct email addresses.

    This allows administrators to override or extend recipients for Alerts
    by assigning specific people or emails to a role.
    """

    role = models.ForeignKey(Role, on_delete=models.CASCADE, verbose_name="نقش")
    persons = models.ManyToManyField(Person, blank=True, verbose_name="افراد")
    emails = models.JSONField(default=list, blank=True, verbose_name="ایمیل‌های مستقیم")
    active = models.BooleanField(default=True, verbose_name="فعال")

    class Meta:
        verbose_name = "نگاشت دریافت‌کننده"
        verbose_name_plural = "نگاشت‌های دریافت‌کننده"

    def __str__(self):
        return f"نگاشت {self.role.name} -> {self.persons.count()} افراد + {len(self.emails)} ایمیل"


class ChannelSettings(models.Model):
    """Global settings for alert delivery channels.

    A single-row model that controls whether email/SMS channels are enabled
    and provides default sender addresses/numbers. If no row exists, tasks
    should fall back to sensible defaults to preserve existing behavior.
    """

    enable_email = models.BooleanField(default=True, verbose_name="فعال‌سازی ایمیل")
    enable_sms = models.BooleanField(default=False, verbose_name="فعال‌سازی پیامک")
    default_from_email = models.CharField(max_length=200, blank=True, verbose_name="ایمیل فرستنده پیش‌فرض")
    default_from_number = models.CharField(max_length=32, blank=True, verbose_name="شماره فرستنده پیامک")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخرین بروزرسانی")

    class Meta:
        verbose_name = "تنظیمات کانال‌ها"
        verbose_name_plural = "تنظیمات کانال‌ها"

    def __str__(self):
        return "تنظیمات کانال‌ها"


class E2ERun(models.Model):
    """Record of E2E test runs triggered from Admin or CI.

    Stores timestamp, method run, stdout/stderr output and a simple success flag.
    """

    METHOD_CHOICES = [("email", "Email"), ("sms", "SMS"), ("both", "Both")]

    method = models.CharField(max_length=10, choices=METHOD_CHOICES, default="email", verbose_name="روش")
    started_at = models.DateTimeField(auto_now_add=True, verbose_name="شروع")
    finished_at = models.DateTimeField(null=True, blank=True, verbose_name="پایان")
    success = models.BooleanField(default=False, verbose_name="موفق")
    output = models.TextField(blank=True, verbose_name="خروجی")

    class Meta:
        verbose_name = "اجرای E2E"
        verbose_name_plural = "اجرای E2E"
        ordering = ("-started_at",)

    def __str__(self):
        return f"E2E {self.method} @ {self.started_at:%Y-%m-%d %H:%M:%S} - {'OK' if self.success else 'FAIL'}"


class E2ESchedule(models.Model):
    """Simple schedule for running E2E tests.

    This is a lightweight scheduler model: a system cron or Celery Beat job can
    call the management command `run_scheduled_e2e` to execute enabled schedules.
    """

    TYPE_CHOICES = [("hourly", "Hourly"), ("daily", "Daily"), ("weekly", "Weekly")]

    name = models.CharField(max_length=150, verbose_name="نام")
    enabled = models.BooleanField(default=True, verbose_name="فعال")
    schedule_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default="daily", verbose_name="نوع برنامه")
    # time of day for daily/weekly schedules
    time_of_day = models.TimeField(null=True, blank=True, verbose_name="زمان روز")
    # day of week for weekly schedules (0=Monday..6=Sunday)
    day_of_week = models.IntegerField(null=True, blank=True, verbose_name="روز هفته")
    method = models.CharField(max_length=10, choices=E2ERun.METHOD_CHOICES, default="email", verbose_name="روش")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="ایجاد‌شده")

    class Meta:
        verbose_name = "زمان‌بندی E2E"
        verbose_name_plural = "زمان‌بندی‌های E2E"

    def __str__(self):
        return f"{self.name} ({self.schedule_type})"
