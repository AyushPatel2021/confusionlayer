#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

compose_files=(-f docker-compose.yml)
if [[ "${CONFUSIONLAYER_NGINX_PROXY:-1}" == "1" && -f docker-compose.nginx.yml ]]; then
  compose_files+=(-f docker-compose.nginx.yml)
fi

git pull --ff-only
docker compose "${compose_files[@]}" up -d --build
docker compose "${compose_files[@]}" ps
