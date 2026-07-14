# ConfusionLayer

AI clears the confusion. Teachers lead the learning.

ConfusionLayer is a predictive, teacher-gated AI learning platform for the OpenAI Build Week Education Track. Teachers unlock chapters classroom-by-classroom; students can only use AI tutorials, doubt chat, quizzes, and teach-back mode for unlocked material. The differentiator is the deterministic Confusion Forecast Engine: it predicts which upcoming concepts students are likely to struggle with from decayed prerequisite mastery before the lesson starts.

## Current Status

Night 1 foundation is scaffolded in this repository:

- Docker Compose stack with `postgres`, `backend`, and `frontend`.
- FastAPI placeholder backend at `/api/health`.
- Vue 3 + TypeScript + Vite + Pinia + Vue Router + Tailwind placeholder frontend.
- Caddy-based static frontend container with API reverse proxy.
- SQLAlchemy models for the Project Spec Section 4 schema.
- Alembic initialized with the first migration.
- Idempotent Night 1 seed script for the demo classroom data.
- Deterministic mastery formula implemented as pure tested backend code.
- JWT auth with HttpOnly cookie storage, bearer-token fallback, and `admin`/`teacher`/`student` roles.
- `.env.example` for private deployment values.
- `scripts/redeploy.sh` for one-command redeploys on the VM.

The Oracle VM at `80.225.232.209` is reachable and already has Docker + Docker Compose installed. It currently runs another nginx-backed deployment for `znova.in`, so ConfusionLayer should not take over ports `80/443` until the subdomain/reverse-proxy choice below is completed.

## Curriculum Source Strategy

ConfusionLayer should be official-aligned, not a copy of textbook content.

Use official public sources for structure and links:

- CBSE Academic curriculum, including the 2026-27 Class X Science curriculum: https://cbseacademic.nic.in/curriculum_2027.html
- NCERT textbook portal for Classes I-XII and chapter/textbook PDFs: https://ncert.nic.in/textbook.php?ln=en
- ePathshala for NCERT e-resources: https://epathshala.nic.in/

Safe usage for this prototype:

- Use board, class, subject, chapter titles, concept names, and syllabus structure.
- Link users to official NCERT/ePathshala resources where useful.
- Store our own concept summaries, learning objectives, allowed/excluded scope, misconception taxonomy, questions, rubrics, and examples.
- Let GPT-5.6 generate tutorials/questions only from structured concept records, not from a bare chapter name.

Avoid:

- Committing NCERT PDFs or copied chapter files.
- Storing complete textbook chapters in the DB.
- Copying long textbook passages, diagrams, illustrations, or end-of-chapter questions in bulk.
- Using CBSE/NCERT branding in a way that implies endorsement.

Planned content pipeline:

```text
Official syllabus structure
        ↓
Manually curated concept map
        ↓
Original learning objectives + allowed/excluded scope
        ↓
GPT-5.6 generates tutorials/questions inside that scope
```

For the hackathon, keep scope tight: one board, one class, one subject, one highly polished functional chapter, plus locked downstream concepts where needed for the forecast engine. A broad automated curriculum importer is intentionally deferred until the core demo works.

Disclaimer:

> ConfusionLayer is an independent educational prototype and is not affiliated with or endorsed by CBSE or NCERT. Curriculum references are used for educational alignment. Official textbooks remain available through NCERT and ePathshala.

## Project Spec Alignment

The implementation is tracking `../PROJECT_SPEC.md`.

Night 1 / Section 3.1:

- [x] Oracle VM reachable by SSH at `ubuntu@80.225.232.209`.
- [x] Public IP confirmed as `80.225.232.209`.
- [x] Docker installed on the VM.
- [x] Docker Compose installed on the VM.
- [x] `docker-compose.yml` created with `postgres`, `backend`, and `frontend`.
- [x] Postgres runs on the internal Docker network only; no host port is exposed by this stack.
- [x] `.env.example` created; real `.env` stays uncommitted.
- [x] Redeploy script created.
- [x] ConfusionLayer subdomain DNS record created.
- [x] HTTPS confirmed on the final ConfusionLayer domain through nginx + Let's Encrypt.
- [x] Phone-on-mobile-data acceptance test passed.
- [x] SQLAlchemy models created for the full Section 4 schema.
- [x] Alembic initialized.
- [x] First migration created.
- [x] Seed script written.
- [x] Misconception taxonomy hand-written for all seeded concepts.
- [x] Local seed acceptance test passed.

Live placeholder:

```text
https://confusionlayer.znova.in
```

Backend health:

```text
https://confusionlayer.znova.in/api/health
```

Auth endpoints:

- `POST /api/auth/signup` with JSON `{ "email", "password", "role": "admin|teacher|student", "name" }`
- `POST /api/auth/login` with JSON `{ "email", "password" }`
- `POST /api/auth/demo` with JSON `{ "role": "teacher|student" }`
- `GET /api/auth/me`
- `POST /api/auth/logout`

Auth responses include a bearer token and set an `access_token` HttpOnly cookie. API requests may authenticate with either the cookie or `Authorization: Bearer <token>`.

Core learning endpoints:

- `GET /api/demo/context`
- `GET /api/student/syllabus`
- `POST /api/teacher/classrooms/{classroom_id}/chapters/{chapter_id}/unlock`
- `GET /api/concepts/{concept_id}`

## Stack

- Frontend: Vue 3, TypeScript, Vite, Pinia, Vue Router, Tailwind
- Backend: FastAPI
- Database: PostgreSQL
- Deployment: Docker Compose on Oracle Cloud VM
- Edge/static serving: Caddy

## Local Setup

Copy the env template:

```bash
cp .env.example .env
```

Start the stack:

```bash
docker compose up -d --build
```

Smoke test:

```bash
curl http://localhost/api/health
```

Open:

```text
http://localhost
```

Run database migrations:

```bash
export PYTHONPATH=backend
alembic upgrade head
```

Inside the backend container:

```bash
python -m alembic -c alembic.ini upgrade head
```

Load the Night 1 demo seed data:

```bash
export PYTHONPATH=backend
python -m app.seed
```

Local seed acceptance result from 2026-07-14:

- 1 subject, 3 chapters, 15 concepts, 15 concept edges.
- 45 fixed misconception taxonomy rows.
- 10 seeded students.
- 30 quiz attempts and 150 mastery records.
- Clustered misconceptions: `BAL_SUBSCRIPT_CHANGE` and `RXN_ELECTRONEGATIVITY_CONFUSION` each appear for 3 different students on the same concept.
- Mastery review dates span 33 days.

Run backend unit tests:

```bash
PYTHONPATH=backend python -m unittest discover -s backend/tests -v
```

## Environment Variables

Required values live in `.env` and must not be committed.

```bash
SITE_DOMAIN=localhost
POSTGRES_DB=confusionlayer
POSTGRES_USER=confusionlayer
POSTGRES_PASSWORD=change-me
DATABASE_URL=postgresql+psycopg://confusionlayer:change-me@postgres:5432/confusionlayer
OPENAI_API_KEY=sk-...
AI_DAILY_CALL_LIMIT=50
JWT_SECRET=change-this-to-a-long-random-secret
JWT_EXPIRES_HOURS=24
AUTH_COOKIE_SECURE=0
```

Use `AUTH_COOKIE_SECURE=1` on HTTPS deployments.

## Oracle VM Deployment Notes

SSH:

```bash
ssh -i ~/.ssh/oracle_key ubuntu@80.225.232.209
```

Observed on 2026-07-14:

- OS: Ubuntu 24.04.4 LTS
- Docker: installed
- Docker Compose: installed
- Current public IP: `80.225.232.209`
- Current `A` records:
  - `znova.in -> 80.225.232.209`
  - `www.znova.in -> 80.225.232.209`
  - `confusionlayer.znova.in -> 80.225.232.209`
- Existing listeners:
  - `22` SSH
  - `443` nginx for `znova.in`
  - `8080` nginx/backend path for the existing project
  - `8000` uvicorn for the existing project
  - `5432` local-only Postgres
- Public `80/443` are handled by nginx; ConfusionLayer runs internally on `127.0.0.1:18080`.

### DNS/Subdomain Work Needed

DNS record now points to the VM:

```text
confusionlayer.znova.in  A  80.225.232.209
```

Alternative if using DuckDNS:

```text
your-confusionlayer-name.duckdns.org  A  80.225.232.209
```

HTTPS is currently issued by Certbot/Let's Encrypt on nginx.

### Port 80/443 Decision

The VM already uses nginx on `443` for `znova.in`. Choose one of these before final HTTPS deployment:

1. Preferred for the spec: migrate edge traffic to Caddy and let this Compose stack bind `80/443`.
2. Lowest-risk with the current VM: keep nginx on `80/443`, run the ConfusionLayer frontend container on an internal port, and add an nginx server block for `confusionlayer.znova.in`.

For the current VM, use the nginx override so the app stays internal and nginx owns public `80/443`:

```bash
docker compose -f docker-compose.yml -f docker-compose.nginx.yml up -d --build
```

Do not run plain `docker compose up` on the VM while nginx is serving `znova.in`, because the base Compose file maps public `80/443`.

Current VM deployment command:

```bash
cd /home/ubuntu/confusionlayer
docker compose -f docker-compose.yml -f docker-compose.nginx.yml up -d --build
```

## Redeploy

After the repo is cloned on the VM and `.env` is created:

```bash
./scripts/redeploy.sh
```

The script runs `docker-compose.nginx.yml` by default when it exists, so Oracle redeploys stay behind nginx:

```bash
git pull --ff-only
docker compose -f docker-compose.yml -f docker-compose.nginx.yml up -d --build
docker compose -f docker-compose.yml -f docker-compose.nginx.yml ps
```

For a direct Caddy deployment that binds public `80/443`, run with:

```bash
CONFUSIONLAYER_NGINX_PROXY=0 ./scripts/redeploy.sh
```

## Placeholder Endpoints

- Frontend: `/`
- Backend health: `/api/health`

## Evaluation Table

Fill this only with real results after the fixed test set is written and run.

| Metric | Result |
|---|---:|
| Structured output success | TBD / 30 |
| Correctness classification accuracy | TBD / 30 |
| Misconception code match accuracy | TBD / 30 |
| Out-of-scope redirection | TBD / 5 |
| Turn-1 direct-answer leakage | TBD / 5 |
| Forecast engine sensitivity check | TBD |
