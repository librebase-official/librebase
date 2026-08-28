#!/usr/bin/env bash
# Librebase production deploy (run by Shiphook after `git pull`).
# Builds the Studio image with the tracked VERSION, recreates the container,
# then waits (with retries) for each health endpoint instead of failing on a
# still-booting container.
#
# LIB-21: Git tracks this file as 100755. If Shiphook spawn() hits EACCES,
# invoke via bash (see docs/shiphook-deploy.md) or chmod +x this path — do
# not rely on a working tree that lost the execute bit (core.fileMode false).
set -Eeuo pipefail
cd /opt/librebase

LIBREBASE_VERSION="$(cat VERSION)"
echo "Deploying Librebase v${LIBREBASE_VERSION}"

docker compose -f data-studio-ui/docker-compose.yml build --no-cache \
  --build-arg "LIBREBASE_VERSION=${LIBREBASE_VERSION}" web
docker rm -f librebase_web_1 2>/dev/null || true
docker compose -f data-studio-ui/docker-compose.yml up -d --force-recreate web

check_path() {
  local path="$1"
  local code=""
  for _ in $(seq 1 30); do
    code=$(curl -sk -o /dev/null -w "%{http_code}" --max-time 5 "http://127.0.0.1:3005${path}" 2>/dev/null || echo 000)
    [ "$code" = "200" ] && return 0
    sleep 2
  done
  echo "health check failed: ${path} (last code: ${code})" >&2
  return 1
}

for path in /api/mcp /.well-known/mcp.json /.well-known/oauth-authorization-server /for-agents; do
  check_path "$path" || exit 1
done

echo "Librebase v${LIBREBASE_VERSION} production deployment healthy"
