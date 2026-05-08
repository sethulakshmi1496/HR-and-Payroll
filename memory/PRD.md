# AEC HR SuperApp — PRD

## Original problem statement
Build the AEC Group HR & Payroll Super App with:
- Prompt 1 (Foundation): Departments, Profiles, Incentives, RBAC ✅ (pre-existing)
- Prompt 2 (Onboarding): Invite/Verify/PDF flow ✅ (pre-existing)
- Prompt 3 (Attendance): GPS geofence, face capture, Cinema skip, dashboard heatmap
- Prompt 4 (Payroll): basic/30 daily, OT, incentives, Kerala PT slabs, ESI/PF, slip PDF

## Tech stack
- Django 5.2 (server-rendered templates + Tailwind via CDN)
- SQLite, Django Q2 (sync mode), ReportLab, Leaflet, Chart.js, face-api.js (CDN)
- Auth: Django session-based (`/accounts/login/`)
- Served via uvicorn ASGI (8001) + runserver (3000) for preview URL routing

## User personas
- **MD** — full power, only one allowed to add/delete incentives.
- **HR** — generate/approve payroll, invite/verify candidates, dashboard.
- **Department Head** — review own dept (48-hour window).
- **Staff** — clock in/out, view own attendance & payslips.

## Implemented (May 2026)
### Prompt 3 — Attendance (verified existing + added)
- ClockInOutView (GPS + base64 face image + IP fallback) ✅
- Haversine geofence (100m, configurable) ✅
- Cinema dept skip in late-flag signal ✅
- **NEW**: timezone-aware late check (was buggy — comparing UTC to local 9 AM)
- **NEW**: dispatch via django-q2 async_task (sync in dev)
- **NEW**: Chart.js heatmap (dept presence %) on dashboard
- Leaflet live map ✅
- Templates extend `onboarding/base.html` ✅

### Prompt 4 — Payroll (built from scratch)
- `payroll.service.PayrollService` — pure compute
  - daily = basic / 30 (fixed)
  - gross = days_present × daily + OT × 2 × daily + incentives
  - PT (Kerala half-yearly), ESI 0.75% if gross<21k, PF 12% capped at ₹15k basic
- `generate_for_profile()` / `generate_for_month()` — idempotent persistence
- `scheduled_monthly_generation()` — django-q2 hook (28th of month)
- `payroll.pdf.build_payslip_pdf()` — ReportLab structured slip
- `PayrollDashboardView` — month selector, table, history Chart.js, MD-only incentive editor
- `GenerateView` — bulk/single, console-email heads
- `ApproveView` — approve & finalize states
- `SlipView` — staff own / HR-MD any
- `TaxPageView` — PT slab table, ESI/PF totals, municipal/building/stationery
- IncentiveAdd / IncentiveDelete (MD only)

### Cross-cutting
- `/accounts/login/` Django built-in LoginView + custom Tailwind template
- `/dashboard/` tile menu home
- CSRF_TRUSTED_ORIGINS for Emergent preview URLs
- Frontend supervisor slot now runs `manage.py runserver 0.0.0.0:3000`

## Backlog / Not implemented
- P1: HTML email templates (currently plain text via console backend)
- P1: Replace `Q_CLUSTER['sync']=True` with real worker (`python manage.py qcluster`)
- P1: 28th-of-month scheduled task auto-registration
- P2: HR view of pending leave requests
- P2: Document vault re-upload (currently locked after verification)
- P2: Multi-language UI (Malayalam toggle)
- P2: Real-time presence websocket
- P2: Two-factor auth for MD

## Test flows
1. Login as MD/HR → /dashboard/ tiles
2. Generate payroll → status flips to HEAD_REVIEW → approve → finalize
3. Download payslip PDF (200 + valid PDF magic bytes)
4. PT calc spot-check: ₹30k basic in Aug → ₹1250 ✓ (matches spec)
5. Cinema dept never sets is_late=True (signal early-return)
