# AEC HR SuperApp — PRD

## Original problem statement
Build the AEC Group HR & Payroll Super App with:
- Prompt 1 (Foundation): Departments, Profiles, Incentives, RBAC ✅
- Prompt 2 (Onboarding): Invite/Verify/PDF flow ✅
- Prompt 3 (Attendance): GPS geofence, face capture, Cinema skip, dashboard heatmap ✅
- Prompt 4 (Payroll): basic/30 daily, OT, incentives, Kerala PT, ESI/PF, slip PDF ✅
- P1+P2 enhancements (May 2026): qcluster + scheduler + leave + i18n + 2FA + doc-vault + live presence + HTML emails ✅
- Prompt 5 (Leaves quota / Holidays / Discipline / Comm / Assets) ✅

## Tech stack
- Django 5.2 (server-rendered Tailwind CDN templates)
- SQLite, **Django Q2** (real worker via supervisor `qcluster`), ReportLab, Leaflet, Chart.js, face-api.js (CDN)
- **django-otp** + **otp_totp** + **qrcode[pil]** (MD 2FA)
- Auth: Django session-based (`/accounts/login/`)
- Served via uvicorn ASGI (8001) + runserver shim (3000) for preview URL routing
- i18n: English + Malayalam

## Implemented (Prompt 5 — May 2026 iteration_3)
### Leave
- **Quota enforcement** in `LeaveCreateView`: probation = 2 half-days/mo, permanent = 4 half-days/mo (HALF=1, FULL/SICK/EMERGENCY = 2 × duration_days). Server-side, both dates parsed before model instantiation.
- **Calendar** at `/leave/calendar/` — month grid showing approved/pending leaves + active holidays.
- **Approval-chain redirect** dropdown on each pending leave row — manager/HR/MD/DEPT_HEAD redirects to another approver while keeping status PENDING; appends note + AuditLog + emails the new approver.

### Holidays
- **HR CRUD** at `/leave/holidays/` — list/add/toggle/delete. Source badge (Kerala public vs Custom).
- **Auto-fetch** task `leave.tasks.holiday_fetch_kerala(year)` — seeds 15 Kerala public holidays for 2026 idempotently. Schedule `kerala-holiday-fetch-yearly` runs every Jan 1.
- **Manual refetch** button on holidays page.

### Discipline
- New `assets.DisciplineRecord` model (severity: WARN/HALF/FULL, deduction_days, attendance FK, is_active for revocation).
- **Late escalation** in `attendance/signals._escalate_discipline()`:
  - 1st late event → no record
  - 2nd → `WARN` + HTML warning email to employee + dept head
  - 3rd → `DEDUCT_HALF_DAY` (0.5 d cut)
  - 4th+ → `DEDUCT_FULL_DAY` (1.0 d cut each)
  - **Cinema dept exempt** (signal short-circuits on `is_cinema=True`)
- **HR review page** `/assets/discipline/` with revoke/restore action.
- **Payroll integration** — `payroll.service.PayrollService.get_discipline_deduction_days()` reads active records; subtracted from gross. Persisted to `Payroll.late_deduction_days` + `Payroll.other_deductions`.

### Communications (Twilio stub)
- `leave.tasks.birthday_sms()` — daily; sends SMS for staff with matching DOB.
- `leave.tasks.anniversary_sms()` — daily; sends SMS for joining-date matches (≥1 yr).
- Both schedules registered (`birthday-sms-daily`, `anniversary-sms-daily`) at 08:00.
- Twilio `_twilio_send_sms_stub` logs to qcluster output (replace with `twilio.rest.Client` in prod).

### Assets / NOC
- New `assets/` app with **CompanyAsset** (PHONE/SIM/LAPTOP/ID_CARD/EQUIPMENT/OTHER + status + return tracking), **NOC** (template upload, signed upload, status flow DRAFT→ISSUED→SIGNED→CLOSED).
- HR/MD: issue + return assets, issue NOCs.
- Staff: view own assets + upload signed NOCs.
- Aadhaar already stored as masked field on `EmployeeProfile.aadhaar_masked`.

### Payroll work_days fix
- `working_days_in_month(year, month, dept=None)` now uses `dept.get_work_days_list()` and subtracts active `Holiday` rows applicable to dept (or global). Cinema/Residency depts include Sundays.

## Test summary
- **iteration_1**: 17/17 PASS (foundation + Prompts 1-4)
- **iteration_2**: 12/12 PASS (P1+P2 enhancements)
- **iteration_3**: 21/21 PASS (Prompt 5 missing items)
- All Python lint clean.

## Routes (current)
| Path | Purpose | Roles |
|---|---|---|
| `/accounts/login/` | Login | All |
| `/dashboard/` | Tile menu | All authed |
| `/onboarding/invite/` | Invite candidate | HR/MD |
| `/onboarding/hr/verify/` | Verify candidates + unlock locked profiles | HR/MD |
| `/attendance/clock/` | Clock in/out | All authed |
| `/attendance/dashboard/` | Heatmap + history + live map | All authed |
| `/attendance/api/live/` | JSON polling for live updates | HR/MD/DEPT_HEAD |
| `/payroll/` | Payroll dashboard | All authed |
| `/payroll/generate/` | Generate drafts | HR/MD |
| `/payroll/approve/<pk>/` | Approve/finalize | HR/MD |
| `/payroll/slip/<y>/<m>/` | Download payslip PDF | All authed |
| `/payroll/tax/` | PT slabs + statutory | HR/MD |
| `/payroll/incentive/{add,delete}/` | Manage incentives | MD only |
| `/leave/` | Leave list + redirect dropdown | All authed |
| `/leave/new/` | Create leave (quota enforced) | All authed |
| `/leave/<pk>/decision/` | Approve/reject/redirect | HR/MD/DEPT_HEAD |
| `/leave/<pk>/cancel/` | Cancel own pending | Self |
| `/leave/calendar/` | Month grid w/ leaves + holidays | All authed |
| `/leave/holidays/` | Kerala holidays CRUD | HR/MD |
| `/leave/holidays/{add,fetch,<pk>/toggle,<pk>/delete}/` | Holiday actions | HR/MD |
| `/assets/` | Assets dashboard | All authed |
| `/assets/{issue,<pk>/return}/` | Issue/return asset | HR/MD |
| `/assets/noc/{issue,<pk>/sign,<pk>/template}/` | NOC flow | HR/MD/Self |
| `/assets/discipline/` | Discipline records | HR/MD |
| `/assets/discipline/<pk>/revoke/` | Toggle active | HR/MD |
| `/2fa/{setup,verify,disable}/` | TOTP 2FA | MD |
| `/i18n/setlang/` | Language switch | All |
| `/admin/` | Django admin | Staff |

## Backlog
- P3: Compile Tailwind into static CSS (replace CDN)
- P3: Recovery codes for MD 2FA
- P3: Native Twilio integration (replace stub)
- P3: Real-time push notifications (channels)
- P3: Expand Kerala holiday seed for 2027/2028
