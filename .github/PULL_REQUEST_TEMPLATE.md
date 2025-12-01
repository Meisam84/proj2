## Summary

Add per-schedule channel overrides to control Email/SMS on a per-schedule basis.

## Changes

- `Schedule` model: `override_enable_email`, `override_enable_sms` (tri-state)
- Helper methods `email_enabled()` and `sms_enabled()`
- Tasks updated to respect per-schedule overrides
- Admin UX: change-form banner, list-editable overrides, bulk actions
- E2E tooling and safe CI workflow added
- Lazy WeasyPrint import via `programs/weasyprint_helper.py` to avoid native deps in CI

## How to test

- Run `python manage.py test programs`
- For E2E smoke: see `.github/workflows/e2e-smoke.yml` (runs locmem email)

## Notes for reviewer

- Ensure admin bulk actions semantics are acceptable
- See `PR_BODY.md` for more details
