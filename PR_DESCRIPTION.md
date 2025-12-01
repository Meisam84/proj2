Title: feature: Per-schedule channel overrides (admin UX, bulk actions, tests, docs)

Summary:
This PR introduces per-schedule channel override capabilities for the alerting system.

Key changes:
- Add tri-state override fields on `Schedule`: `override_enable_email`, `override_enable_sms` (inherit/enabled/disabled).
- Add `email_enabled()` and `sms_enabled()` helpers on `Schedule` to resolve effective behavior (precedence: schedule -> ChannelSettings -> defaults).
- Update `send_alert_email` and `send_alert_sms` tasks to respect per-schedule overrides.
- Improve Admin UX:
  - Read-only informational banner on `Schedule` change form explaining precedence.
  - Show override fields in change form and list-editable columns.
  - Bulk admin actions to set override values across selected schedules.
- Add unit and integration tests covering override logic, tasks behavior, admin bulk actions, and the `send_test_alert` management command.
- Update docs: `docs/runbook/schedule-overrides.md` with operational guidance and screenshot placeholders.

Risk & rollout:
- Backwards-compatible defaults preserved (email considered enabled by default; SMS behavior preserved where no `ChannelSettings` exists).
- Safe for production: admins can apply `inherit` to revert to global behavior; bulk actions require explicit selection.

Testing:
- All new and existing tests pass locally: unit tests and integration tests for tasks and management command.

Notes for reviewers:
- Review admin templates and text for clarity and localization (Persian strings included).
- Consider adding screenshots to `docs/runbook/assets/` for final PR.
