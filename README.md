# Slate

**Run your school. Clear the confusion.**

Slate is a multi-tenant school platform that unifies everyday school operations with an AI
learning engine. Schools, tuition institutes, and individual learners each get a tailored
experience over one system — from admissions and fees to teaching, and to **ConfusionLayer**,
the AI engine that predicts and clears student confusion *before* it derails a lesson.

**Live:** https://confusionlayer.znova.in

> **Status — active development.** The AI learning core (teacher-gated tutoring, misconception
> diagnosis, teach-back, the Confusion Forecast Engine, and student progress) is built and live.
> The full platform — marketing site, real multi-tenant auth, the role hierarchy, curriculum
> authoring/import, and the ERP modules (admissions, fees, HR) — is being built out per the
> roadmap below and detailed in `PRODUCT_PLAN.md`.

## Who it's for

Slate is one engine, packaged for three segments:

- **Schools** — the full stack: an org hierarchy (Owner → School Admin → Accountant / HR /
  Teachers → Students, plus Parents), admissions, fees & accounting, HR & payroll, and the
  learning platform.
- **Tuition institutes** — the teaching + learning core (teachers and students), with optional
  fee tracking.
- **Individual learners** — self-serve access to the ConfusionLayer learning experience.

All plans are currently free.

## ConfusionLayer — the AI learning engine

The differentiator. Instead of only reacting after a student struggles, ConfusionLayer
**forecasts** which upcoming concepts a learner is likely to find hard — from decayed mastery
of prerequisite concepts — and briefs the teacher before the lesson.

- **Teacher-gated AI:** tutorials, Socratic doubt chat (progressive scaffolding), quizzes with
  fixed-taxonomy misconception diagnosis, and teach-back grading.
- **Confusion Forecast Engine:** deterministic graph propagation over the prerequisite map
  (not GPT) that predicts per-concept difficulty. The AI *names* the misconception; the system
  *computes* the mastery and forecast numbers.
- **Teacher briefs:** a predictive Forecast Brief (pre-lesson) and a reactive Confusion Brief
  (aggregated, privacy-thresholded — never individual student names).
- **For students:** mastery-over-time progress and self-start tutorials for any topic.

## Roles & access

Per organization: **Owner, School Admin, Accountant, HR/Staff Manager, Teacher, Student,
Parent** — plus a cross-org **Platform Admin**. Access is role-gated in the UI and authorized
on the backend, with strict per-organization data isolation.

## Curriculum

Curriculum is dynamic and org-authorable: start from a shared library, author
Subjects → Chapters → Topics manually, or **import a document (PDF)** that is auto-structured
into a reviewable subject/chapter/topic tree. Only Owner / School Admin / Teacher roles manage
curriculum.

## Tech stack

- **Frontend:** Vue 3, TypeScript, Vite, Pinia, Vue Router, Tailwind, Chart.js
- **Backend:** FastAPI, SQLAlchemy, Alembic
- **Database:** PostgreSQL
- **AI:** GPT-5.6 via the Codex CLI (`codex exec`, structured output)
- **Deployment:** Docker Compose on an Oracle Cloud VM behind nginx + Let's Encrypt

## Repository layout

```
backend/    FastAPI app, SQLAlchemy models, Alembic migrations, eval harness, tests
frontend/   Vue 3 single-page app
scripts/    redeploy.sh
docker-compose.yml + docker-compose.nginx.yml
```

## Local development

Prerequisites: Docker + Docker Compose. For live AI, run `codex login` on the host first (the
backend mounts `~/.codex`).

```bash
cp .env.example .env
docker compose up -d --build
curl http://localhost/api/health      # smoke test
# open http://localhost
```

Apply migrations and load demo data (inside the backend container):

```bash
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.seed
```

Run backend tests:

```bash
cd backend && python -m pytest
```

## Configuration

All configuration lives in `.env` (never committed). See `.env.example`:

```
SITE_DOMAIN, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD, DATABASE_URL,
CODEX_MODEL, CODEX_TIMEOUT_SECONDS, AI_DAILY_CALL_LIMIT,
JWT_SECRET, JWT_EXPIRES_HOURS, AUTH_COOKIE_SECURE
```

Use `AUTH_COOKIE_SECURE=1` on HTTPS deployments.

## Deployment

Production runs via Docker Compose behind the VM's nginx (which owns public TLS), with the app
bound to loopback. Redeploy with:

```bash
./scripts/redeploy.sh
```

## Roadmap

Full plan in `PRODUCT_PLAN.md`. High level:

1. Design system (in code) + routing shell
2. Multi-tenant data model + real auth / onboarding
3. Segment marketing sites
4. Learning core in the new app shell
5. Curriculum authoring + PDF import
6. Org admin, members & billing (free)
7. ERP: Admissions → Fees / Accounting → HR / Payroll
8. Parent portal, platform admin, polish

## Evaluation

The ConfusionLayer grader/tutor has a fixed evaluation set in `backend/app/eval/`
(correct / partial / misconception grading + doubt-chat redirect and turn-1 leak checks) with
pure, mock-tested scoring and a live runner (`python -m app.eval.run_eval`).

## Curriculum sources & disclaimer

Slate aligns to official public curriculum *structure* (e.g., CBSE / NCERT) without copying
textbook content — structure, titles, and links only; all learner-facing content is original
or AI-generated within a defined scope.

> Slate / ConfusionLayer is an independent educational product and is not affiliated with or
> endorsed by CBSE or NCERT. Curriculum references are used for educational alignment. Official
> textbooks remain available through NCERT and ePathshala.
