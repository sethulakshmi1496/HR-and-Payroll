# AEC HR SuperApp — Zoho-style UI Redesign

## Original Problem
> "give this app a Zoho-style UI."

User confirmed choices (Jan 2026):
- Scope: **Entire app**
- Reference: **Zoho People**
- Theme: **Light + dark toggle**
- Functionality: **only restyle, behavior unchanged**
- Strategy: **Merge into a copy** (placed under /app)

## Architecture
- **Backend**: Django 5.2.14 (ASGI via uvicorn on :8001 wrapped by `/app/backend/server.py`)
- **Frontend shim**: `manage.py runserver 0.0.0.0:3000` (so the public preview URL serves Django).
- **DB**: Postgres (Neon) via `DATABASE_URL` (.env).
- **Modules**: core, onboarding, attendance, payroll, leave, assets, communications, twofa.

## Done in this session — Zoho People restyle
- New design system in `/app/static/css/zoho.css`
  - Light + dark CSS variable tokens (`--bg / --surface / --sidebar / --brand-500 …`)
  - Dark-mode overrides for the Tailwind utility classes already used in module templates (bg-white, text-slate-*, border-slate-*, bg-blue-50/100, etc.)
  - Sidebar + topbar + public auth shell styles
- New authenticated shell in `/app/onboarding/templates/onboarding/base.html`
  - Left sidebar: Dashboard, Attendance, Leave, Payroll, Onboarding, Assets & NOC, Mailers, Clock In/Out
  - Collapsible (mini mode persisted via `localStorage.aec_sidebar_mini`)
  - Active item with blue left-bar accent (path-based detection)
  - Top bar: search, language, theme toggle (sun/moon), notifications, user chip + dropdown menu
  - MD read-only mode rules preserved
- New public auth shell `/app/templates/registration/_base.html` (login/signup extend this)
- Restyled `login.html`, `signup.html`, `setup.html` to Zoho-style centered card with subtle radial brand glow
- Theme toggle (light↔dark) persisted in `localStorage.aec_theme`; applied before paint to avoid FOUC
- `data-testid` added on all new interactive elements (sidebar nav, theme toggle, user menu, login/logout, language switch)
- All existing module pages (attendance, payroll, leave, onboarding, assets, communications, twofa) keep their original markup and inherit the new chrome + dark-mode tokens.

## Verified manually (screenshots)
- Login page – light & dark
- Root Dashboard (HR role) – cards / sidebar
- Attendance Dashboard – chart + map + table, light & dark
- Leave Requests – table, dark
- Payroll – table + form, dark (Approve/Finalize/PDF links readable)
- Onboarding Dashboard – cards, tabs, lifecycle table, dark

## Test credentials
HR user `sethulakshmi` / `test1234` (password reset in this session for QA).

## Next / Backlog
- P1: Add per-module breadcrumbs in the top bar.
- P1: Add a real notifications dropdown (list, mark-as-read).
- P1: Searchbar in topbar can become a global command palette (Ctrl/Cmd+K) — currently visual only.
- P2: Per-user theme stored server-side (currently per-browser via localStorage).
- P2: Hover/focus motion polish on tables, badges and tab transitions.
