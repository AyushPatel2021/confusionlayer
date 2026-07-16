#!/usr/bin/env bash
# Apply database migrations, then start the app. Migrations must succeed before
# the server accepts traffic; a failed migration aborts startup (visible in logs)
# rather than serving against an out-of-date schema.
set -euo pipefail

echo "[entrypoint] applying migrations..."
alembic upgrade head

echo "[entrypoint] starting uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
