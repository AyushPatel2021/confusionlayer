# Infrastructure

This document records the current deployed infrastructure for Slate on the Oracle Cloud VM. It intentionally references secret locations only; it does not include API keys, passwords, JWT secrets, Codex credentials, or tokens.

Last checked: 2026-07-19.

## Live URL

- Production URL: `https://confusionlayer.znova.in`
- Backend health endpoint: `https://confusionlayer.znova.in/api/health`
- Current deployed repo path on VM: `/home/ubuntu/confusionlayer`
- Current deployed runtime commit when checked: `efeaf60`

## What Is Running

Slate runs through Docker Compose in `/home/ubuntu/confusionlayer`.

Current Slate containers:

| Container | Service | Purpose | Network exposure |
|---|---|---|---|
| `confusionlayer-postgres-1` | `postgres` | PostgreSQL 16 database with persistent Docker volume | Internal Docker network only, container port `5432`; not published by this Compose stack |
| `confusionlayer-backend-1` | `backend` | FastAPI app, including auth, learning APIs, Codex subprocess calls, and deterministic forecast engine | Internal Docker network only, container port `8000`; not published by this Compose stack |
| `confusionlayer-frontend-1` | `frontend` | Static Vue build served by Caddy inside the container; proxies `/api` to backend | Published only to VM loopback as `127.0.0.1:18080 -> container:80` |

Public traffic flow:

```text
Browser
  -> https://confusionlayer.znova.in:443
  -> host nginx
  -> http://127.0.0.1:18080
  -> frontend container
  -> backend container for /api requests
  -> postgres container on Docker network
```

Important port state:

- Public `80` and `443`: owned by host nginx.
- Slate frontend: bound on host loopback only at `127.0.0.1:18080`.
- Slate backend: container port `8000`, not published by this Compose stack.
- Slate Postgres: container port `5432`, not published by this Compose stack.
- The VM also has unrelated existing services/listeners for the broader `znova.in` host. Do not treat public `8000`/`8080` listeners as part of Slate unless they are intentionally migrated later.

## Nginx And HTTPS

Host nginx, not Caddy, owns public TLS for Slate.

Relevant nginx files on VM:

- Enabled site: `/etc/nginx/sites-enabled/confusionlayer.znova.in`
- Available site: `/etc/nginx/sites-available/confusionlayer.znova.in`

Current nginx behavior:

- `server_name confusionlayer.znova.in`
- HTTPS listener: `443 ssl`
- HTTP listener: `80`, redirects `confusionlayer.znova.in` to HTTPS
- Reverse proxy target: `http://127.0.0.1:18080`

TLS is managed by Certbot / Let's Encrypt:

- Certificate path: `/etc/letsencrypt/live/confusionlayer.znova.in/fullchain.pem`
- Private key path: `/etc/letsencrypt/live/confusionlayer.znova.in/privkey.pem`
- Current certificate was valid when checked, expiring on `2026-10-12`.

## DNS / Domain

DNS is set up for:

```text
confusionlayer.znova.in -> Oracle VM public IP
```

Observed VM public IP:

```text
80.225.232.209
```

The domain is live over HTTPS and returns `200 OK`.

## VM File Layout

Main app directory:

```text
/home/ubuntu/confusionlayer
```

Important files:

| Path | Purpose |
|---|---|
| `/home/ubuntu/confusionlayer/docker-compose.yml` | Base Compose file for `postgres`, `backend`, and `frontend` |
| `/home/ubuntu/confusionlayer/docker-compose.nginx.yml` | Production override that binds frontend to `127.0.0.1:18080` instead of public `80/443` |
| `/home/ubuntu/confusionlayer/scripts/redeploy.sh` | Standard redeploy script |
| `/home/ubuntu/confusionlayer/.env` | Production environment variables and secrets; do not commit or print values |
| `/home/ubuntu/.codex` | Codex CLI login/session material mounted into backend container as `/root/.codex` |
| `/etc/nginx/sites-available/confusionlayer.znova.in` | Host nginx reverse proxy config |
| `/etc/nginx/sites-enabled/confusionlayer.znova.in` | Symlink to enabled nginx site |

The production `.env` currently defines these keys:

```text
SITE_DOMAIN
POSTGRES_DB
POSTGRES_USER
POSTGRES_PASSWORD
DATABASE_URL
CODEX_MODEL
CODEX_TIMEOUT_SECONDS
AI_DAILY_CALL_LIMIT
JWT_SECRET
JWT_EXPIRES_HOURS
AUTH_COOKIE_SECURE
```

Do not include the values in docs, logs, commits, screenshots, or issue comments.

## Compose Configuration

Base `docker-compose.yml`:

- `postgres`
  - Image: `postgres:16-alpine`
  - Persistent volume: `postgres_data:/var/lib/postgresql/data`
  - Healthcheck uses `pg_isready`
- `backend`
  - Built from `./backend`
  - Runs FastAPI with env from `.env`
  - Mounts `${HOME}/.codex:/root/.codex`
  - Depends on healthy Postgres
- `frontend`
  - Built from `./frontend`
  - Serves the Vue static build through Caddy inside the container
  - In the base file, maps public `80:80` and `443:443`

Production override `docker-compose.nginx.yml`:

```yaml
services:
  frontend:
    ports: !override
      - "127.0.0.1:18080:80"
```

Use the override on the Oracle VM. Without it, the frontend container would try to bind public `80/443`, which conflicts with host nginx and the existing `znova.in` setup.

## Deploy / Redeploy Process

Standard VM deploy command:

```bash
cd /home/ubuntu/confusionlayer
./scripts/redeploy.sh
```

The script lives at:

```text
/home/ubuntu/confusionlayer/scripts/redeploy.sh
```

What it does:

```bash
git pull --ff-only
docker compose -f docker-compose.yml -f docker-compose.nginx.yml up -d --build
docker compose -f docker-compose.yml -f docker-compose.nginx.yml ps
```

The script uses `docker-compose.nginx.yml` by default when `CONFUSIONLAYER_NGINX_PROXY` is unset or set to `1`.

For a direct local deployment that owns public `80/443`, the script can be run with:

```bash
CONFUSIONLAYER_NGINX_PROXY=0 ./scripts/redeploy.sh
```

Do not use that mode on the current Oracle VM unless host nginx is intentionally removed from the deployment architecture.

## Codex / GPT-5.6 Runtime

The backend uses Codex CLI as the production inference path:

```text
codex exec --json --output-schema ...
```

Current live health response reports:

```text
codex_model: gpt-5.6-luna
ai_daily_call_limit: 50
database_configured: true
```

Codex credentials are not in `.env`. They are stored in the VM user's Codex home:

```text
/home/ubuntu/.codex
```

That directory is mounted into the backend container as:

```text
/root/.codex
```

There is no direct OpenAI Platform API fallback path in the app.

## Differences From The Original Plan

The original project plan mentioned Caddy/DuckDNS-style deployment options. The actual live deployment differs:

- Public TLS and reverse proxy are handled by host nginx, not Caddy.
- The app uses the real domain `confusionlayer.znova.in`, not DuckDNS.
- The frontend container still uses Caddy internally to serve static files, but it is not the public edge server.
- The frontend container is bound to `127.0.0.1:18080`; host nginx forwards public HTTPS traffic to that loopback port.
- Postgres remains internal to Docker and is not exposed publicly by the Slate Compose stack.
- GPT-5.6 access is through `codex exec` with persisted Codex login, not a Platform API key.

## Section 3.1 Deployment Checklist Status

| Item | Status | Current evidence |
|---|---|---|
| Provision/confirm Oracle VM reachable | Done | SSH works at `ubuntu@80.225.232.209` |
| Install Docker + Docker Compose | Done | Compose deploy/rebuild is working on VM |
| Compose stack with Postgres/backend/frontend | Done | `docker-compose.yml` defines all three services |
| Persistent Postgres volume | Done | `postgres_data` volume mounted to `/var/lib/postgresql/data` |
| Backend reads DB creds from uncommitted `.env` | Done | `/home/ubuntu/confusionlayer/.env` exists; values are not committed |
| Frontend static build deployed | Done | `frontend` container serves built Vue app |
| Real domain pointed at VM | Done | `confusionlayer.znova.in` resolves to the Oracle VM and serves HTTPS |
| HTTPS working | Done | nginx + Certbot certificate live for `confusionlayer.znova.in` |
| Firewall / exposure: only intended public ports | Mostly done | Slate uses public `80/443` through nginx; its app/db containers are loopback/internal only. VM also has unrelated existing public listeners for another `znova.in` service. |
| Postgres not exposed publicly by Slate | Done | Compose does not publish Postgres; container shows only `5432/tcp` internally |
| `.env` kept out of git | Done | `.env` exists on VM and local but is ignored |
| Placeholder/full stack reachable | Done | `https://confusionlayer.znova.in` returns `200 OK` |
| Redeploy script written | Done | `/home/ubuntu/confusionlayer/scripts/redeploy.sh` |

## Section 3.2 GPT-5.6 / Codex Checklist Status

| Item | Status | Current evidence |
|---|---|---|
| Confirm Codex CLI supports JSON/schema mode | Done | Backend uses `codex exec --json --output-schema` |
| Use `gpt-5.6-luna` model string | Done | Live `/api/health` reports `codex_model: gpt-5.6-luna` |
| Backend calls Codex subprocess for Tutorial Generator | Done | Tutorial contract wired through Codex schema |
| Extend Codex adapter to remaining prompt contracts | Done for core four | Tutorial, Doubt Chat, Quiz Grader, and Teach-Back Grader are wired |
| Production backend authenticated via Codex login | Done | `/home/ubuntu/.codex` is mounted into backend as `/root/.codex` |
| Local hackathon-credit profile separation | Not confirmed in infra | This is a workflow/account-management item, not visible from VM runtime state |
| Latency check for 5 sequential calls | Not completed in infra doc | Avoided here to prevent unnecessary quota spend |
| Concurrency check for 3-5 parallel calls | Not completed in infra doc | Avoided here to prevent unnecessary quota spend |
| Confirm Codex usage/rate-window behavior | Unknown | Needs account-level confirmation, not inferable from VM |
| Remove Platform API key/model env vars | Done | `.env.example` and VM env use Codex settings; no Platform API fallback path |
| Live tutorial endpoint smoke via Codex | Done previously | Live tutorial smoke has passed in prior milestone; not rerun while writing this doc to avoid quota spend |

## Operational Notes

- Do not run plain `docker compose up -d --build` on the VM unless you explicitly intend to bypass host nginx. Use `./scripts/redeploy.sh`.
- Do not print `/home/ubuntu/confusionlayer/.env` values.
- Do not commit `.env` or Codex session files.
- Any runtime change that affects production should be pushed to GitHub first, then pulled on the VM with `git pull --ff-only`, then redeployed.
- After redeploy, verify:

```bash
curl -fsS https://confusionlayer.znova.in/api/health
curl -fsSI https://confusionlayer.znova.in/
```
