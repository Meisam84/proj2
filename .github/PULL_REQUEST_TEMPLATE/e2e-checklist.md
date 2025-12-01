<!--
  E2E PR Template
  - Purpose: ensure repository maintainers run E2E safely (Mailtrap/Twilio) and protect secrets
  - Keep this short, actionable and user-friendly (Persian)
-->

# چک‌لیست اجرای E2E (Mailtrap / Twilio)

- نام شاخهٔ هدف برای E2E: `e2e` (یا از `workflow_dispatch` استفاده کنید).
- قبل از اجرا: اطمینان حاصل کنید که Secrets لازم در **Settings → Secrets and variables → Actions** اضافه شده‌اند:
  - `MAILTRAP_USER`, `MAILTRAP_PASS` (برای Mailtrap)
  - `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM_NUMBER` (برای Twilio)

---

## راهنمای گام‌به‌گام (برای نویسنده PR)

1. بررسی کنید که تغییرات شما نیاز به اجرای E2E دارند.
2. از branch `e2e` استفاده کنید یا از UI GitHub `Run workflow` برای `E2E` اقدام کنید.
3. قبل از اجرای E2E محلی، یک بار `python manage.py send_test_alert --create --method=both` را در محیط محلی با متغیرهای محیطی تست اجرا کنید.
4. پس از اجرای workflow، خروجی Actions را بررسی کنید و خطاهای شبکه/SMTP/Twilio را نگاه کنید.

---

## مواردی که maintainer باید بررسی کند

- آیا Secrets به صورت امن (repository secrets) تنظیم شده‌اند؟
- آیا branch `e2e` محافظت‌شده است و محدودیت‌های push/merge دارد؟
- آیا ایمیل‌ها و پیامک‌های ارسال‌شده به sandbox (Mailtrap/Twilio trial) هستند و نه به کاربران واقعی؟

---

**یادآوری:** این workflow برای توسعه و تست داخلی است؛ از آن در محیط production برای ارسال به کاربران واقعی استفاده نکنید.
