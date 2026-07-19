# Slate Project Overview

This file is the compact source of truth for understanding the product and codebase. Pair it with `DESIGN.md` for visual direction.

## Product Summary

Slate combines a school operating system with ConfusionLayer, a learning engine that predicts and clears confusion before it derails a lesson.

The same codebase supports three paid-product shapes:

- **School:** complete school workspace with ERP modules and learning.
- **Institute:** teaching and learning workspace for tuition/coaching teams.
- **Individual:** self-study workspace for a single learner.

## Core Differentiator

ConfusionLayer is not only a tutorial generator. It stores a curriculum-anchored learner model:

1. Topics live in a subject/chapter/concept graph.
2. Mastery is computed deterministically from attempts, teach-back, misconceptions and retention.
3. Mastery decays over time.
4. Forecast records predict which upcoming concepts are likely to be difficult because prerequisites are weak.
5. AI generates explanations and diagnoses misconceptions, but the system owns the mastery and forecast math.

## User Segments And Roles

### Platform

- **Platform Admin**
  - Sees app-wide workspaces, users, content, usage, revenue signals and audit logs.
  - Does not use school classroom/ERP workflows.

### School

- **School Owner**
  - Full workspace access.
  - Manages members, classrooms, curriculum, admissions, fees, HR, payroll, timetable, attendance and settings.
  - Can connect into active member accounts for demo/support.
- **School Admin**
  - Operational admin access without owner-only billing/member ownership controls.
- **Teacher**
  - Manages assigned classroom learning.
  - Unlocks chapters, views student insights, forecast brief and confusion brief.
- **Student**
  - Sees only own learning workspace.
  - Can access only chapters unlocked for their classroom.
- **Parent**
  - Sees linked child summary, learning progress, attendance and fee signals.
- **Accountant**
  - Fees and account-related workspace.
- **HR**
  - HR/payroll workspace.

### Institute

- **Institute Owner**
  - Manages members, classrooms, curriculum and institute learning.
  - Can invite/connect teacher and student accounts.
- **Institute Teacher**
  - Uses classroom, curriculum and student-insight tools.
- **Institute Student**
  - Uses assigned classroom learning only.

### Individual

- **Individual Student**
  - Creates subjects, chapters and topics.
  - Imports PDFs into a reviewed curriculum tree.
  - All self-study chapters are available; there is no teacher unlock requirement.
  - Uses learn, explore, progress, confusion map, exam outlook and exam practice.

## Major Product Modules

- **Authentication:** email/password signup/login, secure cookie JWT, account profile and password management.
- **Demo access:** sign-in page offers school owner, institute owner, individual learner and platform admin demos.
- **Members:** invitations, role/department assignment, deactivation/removal, owner-only Connect.
- **Classrooms:** create/edit/delete, subject assignment, teacher assignment and student enrollment.
- **Curriculum:** org-scoped subjects, chapters and concepts; shared content remains read-only.
- **PDF import:** file parsed in memory only, optional Codex cleanup, human review before saving.
- **Learning:** syllabus, concept detail, tutorial, doubt chat, quiz grade and teach-back grade.
- **Student progress:** mastery-over-time chart, per-concept mastery and current support needs.
- **Confusion map:** prerequisite readiness and risk view.
- **Exam outlook/practice:** prioritized concepts for exam preparation.
- **Teacher insights:** classroom dashboard, student strengths/weaknesses, prerequisite gaps.
- **Forecast brief:** predicted upcoming struggles with contributors.
- **Confusion brief:** aggregated reactive misconception clusters with privacy threshold.
- **Admissions:** applicant pipeline and enrollment.
- **Fees:** fee structures, invoices, payments, receipts, ledgers and CSV export.
- **HR/payroll:** employees, designations, salary structures, payroll runs, payslips and exports.
- **Attendance:** roll-call workflow and status history.
- **Timetable:** day-wise school operations board.
- **Parent portal:** linked child overview.
- **Platform admin:** app owner dashboard and audit visibility.

## Architecture

```text
Vue SPA
  -> Pinia session store and API client
  -> FastAPI backend
  -> PostgreSQL via SQLAlchemy
  -> Codex CLI subprocess for GPT-5.6 Luna structured outputs
```

Production:

```text
confusionlayer.znova.in
  -> nginx on Oracle VM
  -> frontend container on 127.0.0.1:18080
  -> backend container
  -> postgres container, private Docker network
```

## Backend Structure

```text
backend/app/main.py
  FastAPI routes, response models, permission guards and module handlers.

backend/app/models.py
  SQLAlchemy models for organizations, users, learning, operations and audit.

backend/app/auth.py
  Signup/login, JWT cookies, invitations, demo users and role responses.

backend/app/ai.py
  Codex CLI adapter and structured prompt contracts.

backend/app/briefs.py
  Forecast and confusion aggregation.

backend/app/forecast.py
  Deterministic forecast recomputation.

backend/app/mastery.py
  Mastery decay and effective mastery helpers.

backend/app/curriculum.py
  PDF heading extraction and curriculum import helpers.

backend/app/seed.py
  Rich school, institute, individual and platform demo data.

backend/app/eval/
  Evaluation harness for grader/tutor behavior.
```

## Frontend Structure

```text
frontend/src/router/index.ts
  Auth, role and segment route guards.

frontend/src/stores/session.ts
  Central app state, API calls and typed response interfaces.

frontend/src/layouts/
  Public, app and admin shells.

frontend/src/components/ui/
  Shared controls, loading states, dialogs, badges and chart helpers.

frontend/src/components/app/
  Sidebar, topbar, breadcrumbs, profile menu and app navigation.

frontend/src/views/marketing/
  Public product pages.

frontend/src/views/auth/
  Login, signup, password reset and invitation acceptance.

frontend/src/views/app/
  Role-based school/institute/individual product screens.

frontend/src/views/admin/
  Platform admin dashboard.
```

## AI Contracts

Slate calls Codex CLI instead of the OpenAI Platform API:

```text
codex exec --json --output-schema <schema> <prompt>
```

Contracts:

- Tutorial Generator
- Socratic Doubt Chat
- Quiz Grader / Diagnostician
- Teach-Back Grader
- Forecast/Confusion narrative helpers
- Curriculum import cleanup

Important boundaries:

- AI does not compute final mastery numbers.
- AI must choose from fixed misconception taxonomy where applicable.
- AI calls are rate-limited per user per day.
- Production uses `CODEX_MODEL=gpt-5.6-luna`.

## Data Model Highlights

- `Organization` separates school, institute and individual workspaces.
- `User` stores role, department, org, status and optional linked `Teacher`/`Student`.
- `Subject`, `Chapter`, `Concept`, `ConceptEdge` define curriculum and prerequisites.
- `ChapterUnlock` is per classroom, not global.
- `MasteryRecord` stores current mastery inputs.
- `MasteryHistory` stores chartable time-series snapshots.
- `ForecastRecord` stores deterministic predicted difficulty.
- `QuizAttempt` and `TeachBackAttempt` store learning evidence.
- ERP tables cover admissions, invoices, payments, employees, payroll, attendance and timetable.
- `AuditLog` records sensitive/admin actions.

## Permission Model

- Every API call uses the authenticated cookie session.
- Role checks happen in frontend route guards and backend permission helpers.
- Organization isolation is enforced by org-scoped queries and cross-org guards.
- Platform admin is cross-org but has a separate `/admin` shell.
- School/institute students cannot manage curriculum.
- Individual students can manage only their own self-study curriculum.
- School/institute classroom chapter access requires `ChapterUnlock`.
- Individual self-study concept access does not require `ChapterUnlock`.

## Demo Data

Seed data includes:

- School demo with owner, admin, accountant, HR, teachers, students, parent, curriculum, classrooms, attendance, fees, HR/payroll, admissions and timetable.
- Institute demo with owner, teacher, students, curriculum and classroom learning.
- Individual demo with self-study curriculum and learning/progress data.
- Platform admin demo with app-wide usage/content/audit visibility.

Run:

```bash
docker compose exec backend python -m app.seed
```

Intentional reset:

```bash
docker compose exec -e CONFUSIONLAYER_ALLOW_DB_RESET=1 backend python -m app.seed --reset-demo
```

## Environment And Email

All secrets live in `.env`. `.env.example` lists required and optional variables.

Email behavior:

- If `SMTP_HOST` is set, invitation and password-reset emails are sent over SMTP.
- If SMTP is not set, the email is logged to backend output for local demos.

## Testing

Backend:

```bash
PYTHONPATH=backend python -m pytest backend/tests
```

Frontend:

```bash
cd frontend
npm run build
```

The latest release-readiness audit before this doc cleanup had:

- Backend tests: `148 passed`
- Frontend build: passing
- Live role smoke: school, institute, individual and platform admin API paths returning `200`

## Deployment Notes

Production deploy uses the VM checkout:

```bash
git pull --ff-only
./scripts/redeploy.sh
```

The frontend container is bound to loopback and public traffic is handled by nginx on the VM.

## What To Show In The Demo Video

Recommended flow:

1. Start with the school owner dashboard to show Slate is a real school OS.
2. Open classroom/curriculum to show teacher-gated structure.
3. Switch to a student and show learning, doubt chat, quiz and teach-back.
4. Switch to teacher and show student insights plus forecast brief.
5. Show individual learner briefly to prove self-study curriculum authoring/import.
6. End with platform admin to show app-owner visibility.

Say clearly:

> The AI diagnoses and explains. Slate computes mastery and forecasts deterministically from the learner model.
