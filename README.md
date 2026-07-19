# Slate

**Run your school. Clear the confusion before it starts.**

Slate is a multi-tenant school operating system with ConfusionLayer, an AI learning engine that helps teachers and learners catch gaps before they become exam problems. It supports three product shapes on one codebase:

- **Schools:** full workspace with owner, school admin, accountant, HR, teachers, students, parents, admissions, fees, payroll, timetable, attendance, curriculum and learning.
- **Institutes:** teaching and learning workspace with owners, teachers, students, classrooms, curriculum and learner insights.
- **Individual learners:** self-study workspace where a learner can create/import curriculum, unlock all self-study chapters, learn, practice and track progress.

Live demo: https://confusionlayer.znova.in

## Demo Access

Use the **Explore a demo workspace** section on the sign-in page:

- **School Owner** shows the full school ERP and learning stack.
- **Institute Owner** shows institute member/classroom/curriculum management.
- **Individual Student** shows self-study curriculum, learn, progress, confusion map and exam practice.
- **Platform Admin** shows app-owner usage, content, user and audit visibility.

No demo password is needed for those buttons.

## What Makes It Different

Most AI tutor demos generate explanations after a learner asks for help. Slate adds a persistent model around the learner:

- **Curriculum graph:** subjects, chapters, topics and prerequisite edges.
- **Mastery decay:** deterministic effective mastery from quiz, open answer, misconception recurrence and retention signals.
- **Forecast engine:** pure-code prediction of concepts likely to be difficult next, based on prerequisite gaps.
- **Teacher-gated learning:** school/institute students only access what a teacher unlocks for their classroom.
- **Individual self-study:** individual learners manage their own curriculum and all self-study chapters are available to them.
- **Structured AI contracts:** Codex CLI calls GPT-5.6 Luna for tutorials, Socratic doubt chat, quiz diagnosis, teach-back grading and curriculum cleanup.

The AI explains and diagnoses; the system calculates mastery and forecast numbers deterministically.

## Features

- Real email/password auth with JWT cookie sessions.
- Role and segment routing for platform admin, school owner, school admin, accountant, HR, teacher, student and parent.
- School/institute member invitation flow with optional SMTP delivery.
- Owner-only Connect action for demoing member accounts.
- Classroom CRUD, teacher assignment, student enrollment and subject assignment.
- Dynamic curriculum authoring: subject, chapter and topic manager.
- PDF curriculum import: parses in memory, allows Codex cleanup, then saves reviewed structure.
- Learning flow: syllabus, concept detail, tutorial, doubt chat, quiz grading and teach-back grading.
- Student progress, confusion map, exam outlook and exam practice.
- Teacher classroom view, student insights, forecast brief and confusion brief.
- School operations: admissions, fees, ledgers, receipts, HR, payroll, attendance and timetable.
- Parent portal with learner summary, attendance, fees and learning signals.
- Platform admin dashboard for app-wide usage, content, users and audit logs.

## Tech Stack

- **Frontend:** Vue 3, TypeScript, Vite, Pinia, Vue Router, Tailwind, Chart.js, Lucide icons.
- **Backend:** FastAPI, SQLAlchemy, Alembic, pypdf.
- **Database:** PostgreSQL.
- **AI runtime:** Codex CLI with `gpt-5.6-luna`; no OpenAI Platform API key path.
- **Deployment:** Docker Compose on an Oracle VM, public HTTPS handled by nginx reverse proxy.

## Repository Layout

```text
backend/
  app/
    main.py              FastAPI routes and response models
    models.py            SQLAlchemy tables
    auth.py              auth, invitations, demo users
    ai.py                Codex CLI structured-output adapter
    seed.py              rich demo data
    eval/                grader/tutor evaluation harness
  alembic/               database migrations
  tests/                 backend regression tests

frontend/
  src/
    layouts/             public/app/admin shells
    views/               marketing, auth, app, admin screens
    components/          UI, app shell, charts, marketing pieces
    stores/session.ts    Pinia store and API client
    router/index.ts      route guards and page titles
  public/                Slate SVG logo

scripts/
  redeploy.sh            VM redeploy helper

DESIGN.md                visual system and UI rules
PROJECT_OVERVIEW.md      full product and engineering overview
```

## Local Setup

Prerequisites:

- Docker and Docker Compose
- Codex CLI logged in on the host for live AI calls: `codex login`

```bash
cp .env.example .env
docker compose up -d --build
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.seed
```

Open:

```text
http://localhost
```

Health check:

```bash
curl http://localhost/api/health
```

Reset local demo data intentionally:

```bash
docker compose exec -e CONFUSIONLAYER_ALLOW_DB_RESET=1 backend python -m app.seed --reset-demo
```

## Environment Variables

Copy `.env.example` to `.env`.

| Variable | Purpose |
|---|---|
| `SITE_DOMAIN` | Frontend/Caddy site domain for local compose usage |
| `POSTGRES_DB` | PostgreSQL database name |
| `POSTGRES_USER` | PostgreSQL user |
| `POSTGRES_PASSWORD` | PostgreSQL password |
| `DATABASE_URL` | SQLAlchemy database URL used by backend and Alembic |
| `CODEX_MODEL` | Codex model string, currently `gpt-5.6-luna` |
| `CODEX_TIMEOUT_SECONDS` | Max seconds per Codex subprocess call |
| `AI_DAILY_CALL_LIMIT` | Per-user daily AI call cap |
| `JWT_SECRET` | Long random secret for cookie JWT signing |
| `JWT_EXPIRES_HOURS` | Session lifetime |
| `AUTH_COOKIE_SECURE` | `1` for HTTPS, `0` for local HTTP |
| `SMTP_HOST` | Optional SMTP host for invitation/reset emails |
| `SMTP_PORT` | SMTP port, usually `587` |
| `SMTP_STARTTLS` | `1` to use STARTTLS |
| `SMTP_USERNAME` | Optional SMTP username |
| `SMTP_PASSWORD` | Optional SMTP password |
| `SMTP_FROM` | Sender address for outgoing emails |
| `CONFUSIONLAYER_ALLOW_DB_RESET` | Set to `1` only when intentionally resetting demo data |

Without SMTP settings, emails are logged to backend container logs. This keeps local/demo setup simple while still allowing real invitation email delivery in production.

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

Current verified state before this cleanup:

- Backend tests: `148 passed`
- Frontend production build: passing
- Live smoke: school, institute, individual and platform admin demo paths return `200`

## Deployment

Production runs on the Oracle VM from the git checkout:

```bash
./scripts/redeploy.sh
```

Actual public architecture:

```text
Internet
  -> nginx on VM, HTTPS for confusionlayer.znova.in
  -> frontend container bound on 127.0.0.1:18080
  -> backend container on Docker network
  -> postgres container on Docker network only
```

Production secrets live in the VM `.env` file and are not committed.

## Documentation

- Read `PROJECT_OVERVIEW.md` for the full product, role, architecture, data and demo explanation.
- Read `DESIGN.md` for the visual system.

## Disclaimer

Slate is an independent educational product and is not affiliated with or endorsed by CBSE or NCERT. Curriculum references are used only for educational alignment. Official textbooks remain available through NCERT and ePathshala.
