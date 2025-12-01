# IRIB Programs Management

این پروژه برای مدیریت اطلاعات برنامه‌های رادیویی و تلویزیونی صدا و سیما طراحی شده است.

## ویژگی‌ها
- ثبت، ویرایش و حذف برنامه‌های رادیویی و تلویزیونی
- ذخیره اطلاعات کامل هر برنامه (عنوان، توضیحات، نوع، شبکه، زمان، تهیه‌کننده و ...)
- مناسب برای استفاده در سرورهای درون‌سازمانی

## ساختار اولیه
- Python
- Django

## نحوه اجرا
1. نصب وابستگی‌ها
2. اجرای سرور توسعه

## اجرای Celery (پردازش پس‌زمینه)

برای فعال کردن اسکن دوره‌ای هشدارها این پروژه از Celery با Redis (به‌عنوان broker) استفاده می‌کند.

مثال سریع برای توسعه در ویندوز با Docker (یا جایگزین با WSL):

- راه‌اندازی Redis با Docker:

	docker run -d --name redis -p 6379:6379 redis:7

- اجرای worker در پوشهٔ پروژه (PowerShell):

	$env:CELERY_BROKER_URL = 'redis://localhost:6379/0'; celery -A irib_programs worker -l info

- اجرای beat (scheduler) در ترمینال دیگر:

	$env:CELERY_BROKER_URL = 'redis://localhost:6379/0'; celery -A irib_programs beat -l info

یا برای توسعه می‌توانید worker و beat را همزمان اجرا کنید (توسعه، نه تولید):

	$env:CELERY_BROKER_URL = 'redis://localhost:6379/0'; celery -A irib_programs worker -B -l info

### راه‌اندازی تمام سرویس‌ها با Docker Compose

اگر Docker نصب دارید، می‌توانید سرویس‌های Redis، Django، Celery worker و beat را با یک دستور بالا بیاورید:

```powershell
docker compose up --build
```

برای اجرا در پس‌زمینه:

```powershell
docker compose up -d --build
```

فایل‌های مهم:
- `Dockerfile.dev` - تصویر مورد استفاده در توسعه
- `docker-compose.yml` - سرویس‌های web, redis, worker, beat
- `.env.sample` - نمونهٔ متغیرهای محیطی

## فعال‌سازی ارسال ایمیل (SMTP)

برای ارسال ایمیل‌های هشدار به‌صورت واقعی، تنظیمات SMTP را در متغیرهای محیطی قرار دهید. نمونه‌ای از مقادیر که می‌توانید در فایل `.env` یا در سیستم قرار دهید در `.env.sample` آمده است:


اگر `EMAIL_HOST` تنظیم شود، `settings.py` به طور خودکار از `SMTP` backend استفاده می‌کند. در زمان توسعه می‌توانید از backend کنسول (پیش‌فرض) یا `locmem` برای تست استفاده کنید.

قالب‌های ایمیل HTML و متن در `templates/emails/alert_email.html` و `templates/emails/alert_email.txt` قرار دارند.

## تست‌های انتهاـ‌بهـ‌انتها (E2E) — SMTP و SMS

برای اعتبارسنجی ارسال ایمیل و پیامک در محیط تست (بدون ارسال به گیرنده‌های واقعی) پیشنهاد می‌شود از سرویس‌های آزمایشی استفاده کنید: Mailtrap برای ایمیل و حساب Trial Twilio برای پیامک.

1) Mailtrap (ایمیل):

- در Mailtrap یک inbox بسازید و مقادیر SMTP را بردارید.
- مقادیر زیر را در محیط یا فایل `.env` قرار دهید (نمونه‌ها در `.env.sample` آمده‌اند):

```
EMAIL_HOST=smtp.mailtrap.io
EMAIL_PORT=587
EMAIL_HOST_USER=<MAILTRAP_USER>
EMAIL_HOST_PASSWORD=<MAILTRAP_PASS>
DEFAULT_FROM_EMAIL=no-reply@example.com
```

- سپس از management command محلی استفاده کنید تا یک Alert تستی ساخته و تسک‌ها را اجرا کند:

```powershell
$env:EMAIL_HOST='smtp.mailtrap.io'; $env:EMAIL_PORT='587'; $env:EMAIL_HOST_USER='<MAILTRAP_USER>'; $env:EMAIL_HOST_PASSWORD='<MAILTRAP_PASS>'; $env:DEFAULT_FROM_EMAIL='no-reply@example.com'
python .\manage.py send_test_alert --create --method=email
```

2) Twilio (SMS):

- برای ارسال پیامک آزمایشی با Twilio trial:
	- یک حساب Twilio بسازید و `Account SID`, `Auth Token`, و یک شمارهٔ From را بردارید.
	- این مقادیر را در محیط یا `.env` قرار دهید:

```
TWILIO_ACCOUNT_SID=ACxxxx
TWILIO_AUTH_TOKEN=yourtoken
TWILIO_FROM_NUMBER=+1XXXXXXXXXX
```

- سپس می‌توانید از management command برای ارسال SMS (پیش‌نیاز: فعال‌سازی `ChannelSettings.enable_sms` اگر از Admin استفاده می‌کنید):

```powershell
$env:TWILIO_ACCOUNT_SID='ACxxxx'; $env:TWILIO_AUTH_TOKEN='yourtoken'; $env:TWILIO_FROM_NUMBER='+1XXXXXXXXXX'
python .\manage.py send_test_alert --create --method=sms
```

3) GitHub Actions (اختیاری):

یک workflow نمونه اضافه کردم به `/.github/workflows/e2e.yml` که در صورتی اجرا می‌شود که اسرار (Secrets) لازم را در ریپویتان قرار دهید (`MAILTRAP_USER`, `MAILTRAP_PASS`, `TWILIO_*`). این workflow به صورت ایمن از Secretها استفاده می‌کند و `send_test_alert` را اجرا می‌کند.

نکتهٔ امنیتی: این workflow طوری تنظیم شده است که **فقط** به‌صورت دستی (`workflow_dispatch`) یا در زمان push به شاخهٔ محافظت‌شدهٔ `e2e` اجرا شود. این جلوگیری می‌کند از اجرای ناخواستهٔ E2E در هر PR یا push روی شاخه‌های دیگر.

## محافظت از شاخهٔ `e2e`

برای جلوگیری از اجرای ناخواستهٔ تست‌های E2E و کنترل دسترسی به اسرار (Secrets) که برای Mailtrap/Twilio استفاده می‌شوند، پیشنهاد می‌شود شاخهٔ `e2e` را در ریپوی GitHub خود محافظت کنید. مراحل پیشنهادی:

1. در GitHub به صفحهٔ repository بروید → `Settings` → `Branches` → `Add rule`.
2. در بخش `Branch name pattern` مقدار `e2e` را وارد کنید.
3. فعال کنید `Require pull request reviews before merging` و حداقل 1 reviewer تعیین کنید تا هیچ‌کسی نتواند مستقیم push کند.
4. فعال کنید `Require status checks to pass before merging` و در صورت تمایل CI (jobهای مرتبط) را انتخاب کنید.
5. فعال کنید `Restrict who can push to matching branches` و فقط کاربران یا تیم‌های مشخص را مجاز کنید (معمولاً CI service account یا admins).
6. در `Settings` → `Secrets and variables` → `Actions`، مقادیر `MAILTRAP_USER`, `MAILTRAP_PASS`, `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM_NUMBER` را به‌عنوان Secrets اضافه کنید و دسترسی آن‌ها را محدود به repository نگه دارید.

با این تنظیمات، workflow E2E تنها زمانی اجرا می‌شود که شما عمداً آن را از طریق رابط GitHub یا با push به شاخهٔ `e2e` فعال کنید و Secrets امن بمانند.
> توجه: اجرای E2E در CI نیاز به مراقبت دارد — use sandbox credentials (Mailtrap/Twilio trial) و از ارسال پیام به شماره‌ها/ایمیل‌های واقعی خودداری کنید.

### ارسال پیامک (SMS)

این پروژه می‌تواند در سطح پایه پیامک ارسال کند؛ پیاده‌سازی نمونه با Twilio قابل فعال‌سازی است. برای فعال‌سازی، `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN` و `TWILIO_FROM_NUMBER` را در `.env` قرار دهید. اگر مقادیر تنظیم نشده باشند، task مربوط به ارسال SMS به‌صورت ایمن خطا را باز می‌گرداند و کاری انجام نمی‌دهد.

برای راه‌اندازی واقعی Twilio، کتابخانهٔ `twilio` را نصب کرده و متغیرهای محیطی را تنظیم کنید، سپس می‌توانید از طریق Admin یا taskهای Celery پیامک ارسال کنید.

تنظیمات پیش‌فرض (در irib_programs/settings.py) از آدرس redis://localhost:6379/0 استفاده می‌کند و وظیفهٔ
`programs.tasks.check_alerts_task` هر 5 دقیقه اجرا می‌شود تا Alerts را برای نمونه‌های برنامهٔ تأییدنشده ایجاد کند.

## بازنویسی کانال‌ها در سطح هر برنامه‌ریزی (Per-schedule Overrides)

این پروژه امکان تنظیم رفتار ارسال برای هر ردیف کنداکتور (`Schedule`) را فراهم می‌کند. دو فیلد جدید در مدل
`Schedule` و فرم ادمین وجود دارد:

- `override_enable_email`: سه‌حالته — `inherit` (پیش‌فرض، استفاده از `ChannelSettings`)، `enabled`، `disabled`.
- `override_enable_sms`: سه‌حالته — `inherit`, `enabled`, `disabled`.

قواعد تصمیم‌گیری (ترتیب تقدم):

1. اگر مقدار فیلد مربوط در `Schedule` روی `enabled` یا `disabled` تنظیم شده باشد، آن مقدار اعمال می‌شود.
2. در حالت `inherit`، تنظیمات سراسری در `ChannelSettings` بررسی می‌شود.
3. اگر هیچ تنظیم سراسری‌ای وجود نداشته باشد، پیش‌فرض‌های منطقی اعمال می‌شود: ایمیل `True`، پیامک `False`.

این مکانیزم به مدیران اجازه می‌دهد که برای برنامه‌های حساس یا زمان‌بندی‌های خاص، ارسال ایمیل یا پیامک را
غیرفعال کنند یا اجباری سازند بدون تغییر در تنظیمات سراسری.

نکته‌های کاربردی:

- فیلدها در فرم ادمین `Schedule` نمایش داده می‌شوند و در نمای لیست نیز قابل ویرایش سریع هستند.
- توابع کمکی `email_enabled()` و `sms_enabled()` در مدل `Schedule` برای تعیین نهایی استفاده می‌شوند؛ کد تسک‌ها
	(`programs.tasks`) از این توابع برای تصمیم‌گیری قبل از ارسال استفاده می‌کند.
- تست‌های واحد برای این منطق در `programs/tests/test_schedule_overrides.py` و `programs/tests/test_tasks_schedule_overrides.py` موجودند.

مثال:

اگر بخواهید ایمیل را برای یک ردیف خاص غیرفعال کنید، وارد ادمین شده، ردیف `Schedule` مربوطه را باز کنید و
در بخش `بازنویسی: ایمیل` مقدار `غیرفعال` را انتخاب کنید. سپس هر تسکی که تلاش به ارسال ایمیل برای آن برنامه‌ریزی کند
با خطای `email_disabled_by_schedule` مواجه می‌شود و ارسال انجام نخواهد شد.

---
