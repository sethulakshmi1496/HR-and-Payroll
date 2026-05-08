# AEC HR SuperApp — PRD

## Original problem statement
Build the AEC Group HR & Payroll Super App with:
- Prompt 1 (Foundation): Departments, Profiles, Incentives, RBAC ✅
- Prompt 2 (Onboarding): Invite/Verify/PDF flow ✅
- Prompt 3 (Attendance): GPS geofence, face capture, Cinema skip, dashboard heatmap ✅
- Prompt 4 (Payroll): basic/30 daily, OT, incentives, Kerala PT, ESI/PF, slip PDF ✅
- P1+P2 enhancements (May 2026): qcluster + scheduler + leave + i18n + 2FA + doc-vault + live presence + HTML emails ✅

## Tech stack
- Django 5.2 (server-rendered Tailwind CDN templates)
- SQLite, **Django Q2** (real worker via supervisor `qcluster`), ReportLab, Leaflet, Chart.js, face-api.js (CDN)
- **django-otp** + **otp_totp** (TOTP) + **qrcode[pil]** (MD 2FA)
- Auth: Django session-based (`/accounts/login/`)
- Served via uvicorn ASGI (8001) + runserver shim (3000) for preview URL routing
- i18n: English + Malayalam (`locale/ml/LC_MESSAGES/django.{po,mo}`)

## User personas
- **MD** — full power; **TOTP 2FA enforced**; only role allowed to add/delete incentives.
- **HR** — generate/approve payroll, invite/verify candidates, approve leave, unlock/relock locked profiles for re-upload.
- **Department Head** — review own dept (48-hour window), approve own dept's leave.
- **Staff** — clock in/out, view own attendance/payslips, request/cancel own leave.

## Implemented (May 2026)
### Foundation + Prompt 3 (Attendance) + Prompt 4 (Payroll) — see iteration_1 testing.

### P1 Enhancements
- **Real qcluster worker** — `/etc/supervisor/conf.d/qcluster.conf`. `Q_CLUSTER['sync']` is now config-driven (default False). 2 workers, ORM broker.
- **28th-of-month auto-schedule** — `payroll/migrations/0001_register_schedule.py` registers `Schedule(name='payroll-monthly-28th', func='payroll.service.scheduled_monthly_generation', schedule_type=MONTHLY, next_run.day=28)`.
- **HR Leave Requests** — new `leave/` app: list/create/decision/cancel views; templates with pending + history tables; data-testids for testing; HR/MD/DEPT_HEAD see all (DEPT_HEAD scoped to own dept).
- **HTML email templates** — `twofa.emails.send_html_mail` helper + `templates/email/{base,leave_request,leave_decision,payroll_ready,onboarding_welcome}.html`. EmailMultiAlternatives multipart/alternative (text+html). Replaced plain-text emails in onboarding, payroll, leave flows.

### P2 Enhancements
- **Document vault unlock** — HR action at `/onboarding/hr/unlock/<pk>/`. New "Locked Profiles" section on HR verify page. AuditLog entries on unlock/relock.
- **Malayalam i18n toggle** — `LANGUAGES=[en,ml]` + `LocaleMiddleware`. Language switcher (`/i18n/setlang/`) in nav. Translation file with 60+ strings (nav, leave, 2fa flows).
- **MD-only TOTP 2FA** — `twofa/` app with `SetupView` (QR data URI + hex secret), `VerifyView`, `DisableView`, `EnforceMD2FAMiddleware` (exempts /static, /media, /accounts, /2fa, /admin, /i18n). Uses `django_otp.plugins.otp_totp.TOTPDevice`. Session flag `md_2fa_verified` cleared on logout. MD card on dashboard for setup.
- **Real-time presence** — `/attendance/api/live/` JSON endpoint; dashboard polls every 30s for fresh heatmap + map markers (lighter than Channels websockets, no Redis dependency). Live timestamp shown.

## Test results
- **iteration_1**: 17/17 backend, frontend OK
- **iteration_2** (P1+P2): 12/12 new tests pass; lint clean

## Backlog
- P3: Replace Tailwind CDN with compiled CSS (cosmetic warning)
- P3: Recovery codes for MD 2FA (otp_static plugin already in INSTALLED_APPS — wire UI)
- P3: Async push notifications for leave decisions (currently email only)
- P3: Department Head dashboard with own-dept attendance + leave KPIs
- P3: Self-onboarding face-image library training (improve face-api.js match)

## Routes summary
| Path | Purpose | Roles |
|------|---------|-------|
| /accounts/login/ | Login | All |
| /dashboard/ | Tile menu | All authed |
| /onboarding/invite/ | Invite candidate | HR/MD |
| /onboarding/hr/verify/ | Verify candidates + unlock locked profiles | HR/MD |
| /onboarding/hr/unlock/<pk>/ | Toggle profile lock | HR/MD |
| /attendance/clock/ | Clock in/out | All authed |
| /attendance/dashboard/ | Heatmap + history + live map | All authed |
| /attendance/api/live/ | JSON polling for live updates | HR/MD/DEPT_HEAD |
| /payroll/ | Payroll dashboard | All authed |
| /payroll/generate/ | Generate drafts | HR/MD |
| /payroll/approve/<pk>/ | Approve/finalize | HR/MD |
| /payroll/slip/<y>/<m>/ | Download payslip PDF | All authed |
| /payroll/tax/ | PT slabs + statutory | HR/MD |
| /payroll/incentive/add|delete/ | Manage incentives | MD only |
| /leave/ | Leave list | All authed |
| /leave/new/ | Create leave | All authed |
| /leave/<pk>/decision/ | Approve/reject | HR/MD/DEPT_HEAD |
| /leave/<pk>/cancel/ | Cancel own pending | Self |
| /2fa/setup/ | TOTP setup | MD |
| /2fa/verify/ | TOTP verify | MD |
| /2fa/disable/ | Disable TOTP | MD |
| /i18n/setlang/ | Language switch | All |
| /admin/ | Django admin | Staff |
