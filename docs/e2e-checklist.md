# چک‌لیست ایمن‌سازی و اجرای E2E (Mailtrap / Twilio)

این سند به‌صورت مختصر و کاربرپسند فرآیند ایمن‌سازی، راه‌اندازی و اجرای تست‌های انتها-به-انتهای سرویس‌های ایمیل و پیامک را توضیح می‌دهد.

## پیش‌نیازها

- دسترسی به ریپوزیتوری و قابلیت ایجاد Secrets در GitHub
- یک حساب Mailtrap برای تست ایمیل یا هر SMTP sandbox دیگر
- یک حساب Twilio (trial) برای تست پیامک (اختیاری)

## گام‌های ایمن‌سازی

1. اضافه کردن Secrets به ریپوزیتوری (Settings → Secrets and variables → Actions):
   - `MAILTRAP_USER`, `MAILTRAP_PASS`
   - `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM_NUMBER`
2. محافظت از شاخهٔ `e2e` (Branch protection):
   - Require pull request reviews before merging
   - Restrict who can push to the branch (admins/CI account only)
   - Optionally require status checks
3. استفاده از workflow E2E فقط به‌صورت دستی یا روی شاخهٔ `e2e`.

## اجرای محلی سریع

```powershell
# Mailtrap example
$env:EMAIL_HOST='smtp.mailtrap.io'; $env:EMAIL_PORT='587'; $env:EMAIL_HOST_USER='<MAILTRAP_USER>'; $env:EMAIL_HOST_PASSWORD='<MAILTRAP_PASS>'; $env:DEFAULT_FROM_EMAIL='no-reply@example.com'
python .\manage.py send_test_alert --create --method=email

# Twilio example
$env:TWILIO_ACCOUNT_SID='ACxxxx'; $env:TWILIO_AUTH_TOKEN='token'; $env:TWILIO_FROM_NUMBER='+1XXXXXXXXXX'
python .\manage.py send_test_alert --create --method=sms
```

## پس از اجرای E2E

- بررسی لاگ‌های workflow در GitHub Actions
- اطمینان از اینکه پیام‌ها در Mailtrap (inbox) ظاهر شده‌اند و شماره‌های تست در Twilio logs آمده‌اند
- در صورت خطا، بررسی مقادیر environment، اتصال شبکه و پیام خطا در Sentry

## نکات کاربردی

- همیشه با sandbox (Mailtrap/Twilio trial) کار کنید؛ از ارسال مستقیم به کاربران واقعی خودداری کنید.
- برای هر اجرای E2E، یک PR مختصر با خروجی Actions و اسکرین‌شات‌های Mailtrap/Twilio ارسال کنید تا تاریخچهٔ تست حفظ شود.
