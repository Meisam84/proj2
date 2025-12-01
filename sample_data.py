"""
نمونه برای ورود اطلاعات اولیه

برای استفاده از این نمونه:
1. python manage.py shell
2. exec(open('sample_data.py').read())
"""

from datetime import timedelta

from django.utils import timezone

from programs.models import (
    Channel,
    Conductor,
    Genre,
    Person,
    Program,
    ProgramGuest,
    ProgramInstance,
    ProgramMember,
    Role,
    Schedule,
    TargetAudience,
)

print("شروع ورود داده‌های نمونه...")

# ============================================================================
# 1. ایجاد شبکه‌ها
# ============================================================================

print("\n✓ ایجاد شبکه‌ها...")

channel_irib1, _ = Channel.objects.get_or_create(
    name="شبکهٔ اول",
    defaults={
        "code": "IRIB1",
        "program_type": "tv",
        "description": "شبکهٔ تلویزیونی اول",
        "is_active": True,
        "latitude": 35.6892,
        "longitude": 51.3890,
        "timezone": "Asia/Tehran",
    },
)

channel_irib2, _ = Channel.objects.get_or_create(
    name="شبکهٔ دو",
    defaults={
        "code": "IRIB2",
        "program_type": "tv",
        "description": "شبکهٔ تلویزیونی دو",
        "is_active": True,
        "latitude": 35.6892,
        "longitude": 51.3890,
        "timezone": "Asia/Tehran",
    },
)

channel_radio, _ = Channel.objects.get_or_create(
    name="رادیو ایران",
    defaults={
        "code": "RADIO1",
        "program_type": "radio",
        "description": "رادیو ایران",
        "is_active": True,
        "latitude": 35.6892,
        "longitude": 51.3890,
        "timezone": "Asia/Tehran",
    },
)

# ============================================================================
# 2. ایجاد ژانرها
# ============================================================================

print("✓ ایجاد ژانرها...")

genres_data = [
    {"name": "خبری", "code": "NEWS"},
    {"name": "ورزشی", "code": "SPORTS"},
    {"name": "فرهنگی", "code": "CULTURE"},
    {"name": "سرگرمی", "code": "ENTERTAINMENT"},
    {"name": "آموزشی", "code": "EDUCATIONAL"},
]

genres = {}
for genre_data in genres_data:
    genre, _ = Genre.objects.get_or_create(**genre_data)
    genres[genre_data["code"]] = genre

# ============================================================================
# 3. ایجاد نقش‌ها
# ============================================================================

print("✓ ایجاد نقش‌ها...")

roles_data = [
    {"name": "تهیه‌کننده", "code": "PRODUCER"},
    {"name": "مجری", "code": "PRESENTER"},
    {"name": "کارگردان", "code": "DIRECTOR"},
    {"name": "نویسنده", "code": "WRITER"},
    {"name": "فیلم‌نامه‌نویس", "code": "SCREENWRITER"},
]

roles = {}
for role_data in roles_data:
    role, _ = Role.objects.get_or_create(**role_data)
    roles[role_data["code"]] = role

# ============================================================================
# 4. ایجاد افراد
# ============================================================================

print("✓ ایجاد افراد...")

persons_data = [
    {"full_name": "احمد حسینی", "email": "ahmad@example.com", "phone": "09121234567"},
    {"full_name": "مریم رحیمی", "email": "maryam@example.com", "phone": "09129876543"},
    {"full_name": "علی کریمی", "email": "ali@example.com", "phone": "09123456789"},
    {"full_name": "فاطمه محمدی", "email": "fatima@example.com", "phone": "09125555555"},
]

persons = {}
for person_data in persons_data:
    person, _ = Person.objects.get_or_create(
        full_name=person_data["full_name"],
        defaults={"email": person_data["email"], "phone": person_data["phone"], "is_active": True},
    )
    persons[person_data["full_name"]] = person

# ============================================================================
# 5. ایجاد مخاطبین هدف
# ============================================================================

print("✓ ایجاد مخاطبین هدف...")

audiences_data = [
    {"name": "کودکان", "age_min": 3, "age_max": 12},
    {"name": "نوجوانان", "age_min": 13, "age_max": 18},
    {"name": "بزرگسالان", "age_min": 19, "age_max": 60},
    {"name": "سالمندان", "age_min": 60, "age_max": 150},
]

audiences = {}
for aud_data in audiences_data:
    audience, _ = TargetAudience.objects.get_or_create(**aud_data)
    audiences[aud_data["name"]] = audience

# ============================================================================
# 6. ایجاد برنامه‌ها
# ============================================================================

print("✓ ایجاد برنامه‌ها...")

# برنامهٔ اول: صفحهٔ اول
program1, _ = Program.objects.get_or_create(
    title="صفحهٔ اول",
    defaults={
        "subtitle": "برنامهٔ خبری شام",
        "description": "برنامهٔ خبری شام با رویدادهای روز",
        "channel": channel_irib1,
        "default_duration": timedelta(minutes=60),
        "broadcast_type": "live",
        "program_origin": "live",
        "media_source": "studio",
        "is_live": True,
        "is_repeatable": True,
        "is_active": True,
        "language": "fa",
        "keywords": "خبر، سیاست، اقتصاد",
    },
)
program1.genres.add(genres["NEWS"])
program1.target_audiences.add(audiences["بزرگسالان"])

# برنامهٔ دوم: ورزش شب
program2, _ = Program.objects.get_or_create(
    title="ورزش شب",
    defaults={
        "subtitle": "برنامهٔ ورزشی شام",
        "description": "آخرین اخبار ورزشی جهان",
        "channel": channel_irib1,
        "default_duration": timedelta(minutes=45),
        "broadcast_type": "live",
        "program_origin": "produced",
        "media_source": "automation",
        "is_live": True,
        "is_repeatable": True,
        "is_active": True,
        "language": "fa",
        "keywords": "ورزش، فوتبال، لیگ برتر",
    },
)
program2.genres.add(genres["SPORTS"])
program2.target_audiences.add(audiences["بزرگسالان"])

# برنامهٔ سوم: رنگین‌کمان
program3, _ = Program.objects.get_or_create(
    title="رنگین‌کمان",
    defaults={
        "subtitle": "برنامهٔ بچه‌ها",
        "description": "برنامهٔ سرگرمی و آموزشی برای کودکان",
        "channel": channel_irib1,
        "default_duration": timedelta(minutes=30),
        "broadcast_type": "recorded",
        "program_origin": "produced",
        "media_source": "automation",
        "is_live": False,
        "is_repeatable": True,
        "is_active": True,
        "language": "fa",
        "keywords": "بچه‌ها، سرگرمی، آموزش",
    },
)
program3.genres.add(genres["ENTERTAINMENT"], genres["EDUCATIONAL"])
program3.target_audiences.add(audiences["کودکان"])

# ============================================================================
# 7. اختصاص اعضای برنامه
# ============================================================================

print("✓ اختصاص اعضای برنامه...")

# صفحهٔ اول
ProgramMember.objects.get_or_create(
    program=program1, person=persons["احمد حسینی"], role=roles["PRODUCER"], defaults={"is_primary": True}
)
ProgramMember.objects.get_or_create(
    program=program1, person=persons["مریم رحیمی"], role=roles["PRESENTER"], defaults={"is_primary": True}
)

# ورزش شب
ProgramMember.objects.get_or_create(
    program=program2, person=persons["علی کریمی"], role=roles["PRODUCER"], defaults={"is_primary": True}
)
ProgramMember.objects.get_or_create(
    program=program2, person=persons["فاطمه محمدی"], role=roles["PRESENTER"], defaults={"is_primary": True}
)

# ============================================================================
# 8. ایجاد نمونه‌های برنامه
# ============================================================================

print("✓ ایجاد نمونه‌های برنامه...")

now = timezone.now()
today = now.replace(hour=20, minute=0, second=0, microsecond=0)

# نمونهٔ صفحهٔ اول برای امروز
instance1 = ProgramInstance.objects.create(
    program=program1,
    episode_number=1,
    episode_title="شماره‌ی ۱۵ مهر ماه",
    episode_description="اخبار مهم روز: تصویب لایحهٔ جدید",
    scheduled_start=today,
    scheduled_end=today + timedelta(minutes=60),
    status="approved",
)

# نمونهٔ ورزش شب برای امروز
instance2 = ProgramInstance.objects.create(
    program=program2,
    episode_number=2,
    episode_title="شماره‌ی ۲ مهر ماه",
    episode_description="بررسی دیدار دربی تهران و شاگرد",
    scheduled_start=today + timedelta(hours=1, minutes=15),
    scheduled_end=today + timedelta(hours=2),
    status="approved",
)

# ============================================================================
# 9. اضافه‌کردن مهمانان
# ============================================================================

print("✓ اضافه‌کردن مهمانان...")

ProgramGuest.objects.get_or_create(
    program_instance=instance1, person=persons["احمد حسینی"], defaults={"guest_order": 1}
)

# ============================================================================
# 10. ایجاد برنامه‌ریزی
# ============================================================================

print("✓ ایجاد برنامه‌ریزی...")

schedule1 = Schedule.objects.create(
    channel=channel_irib1,
    schedule_date=today.date(),
    program_instance=instance1,
    order=1,
    notes="برنامهٔ معمولی، بدون تغییر",
)

schedule2 = Schedule.objects.create(
    channel=channel_irib1,
    schedule_date=today.date(),
    program_instance=instance2,
    order=2,
    notes="برنامهٔ معمولی، بدون تغییر",
)

# ============================================================================
# 11. ایجاد کنداکتور
# ============================================================================

print("✓ ایجاد کنداکتور...")

conductor1 = Conductor.objects.create(
    schedule=schedule1,
    auto_play_intro=True,
    auto_play_outro=True,
    auto_adjust_volume=True,
    auto_record=True,
    priority=5,
    contact_person=persons["احمد حسینی"],
    special_instructions="توجه: این برنامهٔ مهم است. پخش باید دقیق شروع شود.",
)

conductor2 = Conductor.objects.create(
    schedule=schedule2,
    auto_play_intro=True,
    auto_play_outro=True,
    auto_adjust_volume=False,
    auto_record=True,
    priority=4,
    contact_person=persons["علی کریمی"],
    special_instructions="برنامهٔ معمولی",
)

# ============================================================================
# نتیجه
# ============================================================================

print("\n" + "=" * 60)
print("✅ داده‌های نمونه با موفقیت ورود شدند!")
print("=" * 60)
print("\n📊 خلاصهٔ داده‌های ورود شده:")
print(f"   • شبکه‌ها: {Channel.objects.count()}")
print(f"   • ژانرها: {Genre.objects.count()}")
print(f"   • نقش‌ها: {Role.objects.count()}")
print(f"   • افراد: {Person.objects.count()}")
print(f"   • برنامه‌ها: {Program.objects.count()}")
print(f"   • نمونه‌های برنامه: {ProgramInstance.objects.count()}")
print(f"   • برنامه‌ریزی‌ها: {Schedule.objects.count()}")
print(f"   • کنداکتورها: {Conductor.objects.count()}")
print("\n💻 برای دیدن اطلاعات، به آدرس زیر رفته و وارد شوید:")
print("   http://localhost:8000/admin/")
print("\n👤 نام کاربری: admin")
print("🔐 پسورد: admin123")
print("\n" + "=" * 60)
