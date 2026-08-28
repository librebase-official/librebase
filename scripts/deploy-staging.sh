#!/usr/bin/env bash
# Librebase staging deploy — run on homelab (engine).
# Builds all staging services, recreates containers, and waits for health.
set -Eeuo pipefail

cd "$(dirname "$0")/../deploy/compose"

LIBREBASE_VERSION="$(cat ../../VERSION)"
echo "=== Deploying Librebase staging v${LIBREBASE_VERSION} ==="

# Ensure the staging network exists
docker network create librebase-staging-net 2>/dev/null || true

# Build all images
docker compose -f docker-compose.staging.yml build --no-cache

# Recreate all containers
docker compose -f docker-compose.staging.yml up -d --force-recreate

# Health-check helper
check() {
  local name="$1" url="$2"
  local code=""
  for _ in $(seq 1 30); do
    code=$(curl -sk -o /dev/null -w "%{http_code}" --max-time 5 "$url" 2>/dev/null || echo 000)
    [ "$code" = "200" ] && echo "  ✓ $name" && return 0
    sleep 2
  done
  echo "  ✗ $name (last code: $code)" >&2
  return 1
}

echo ""
echo "Waiting for services..."
ok=true
check "admin-api"   "http://127.0.0.1:54331/health"       || ok=false
check "studio"      "http://127.0.0.1:3007/"               || ok=false
check "studio/mcp"  "http://127.0.0.1:3007/api/mcp"       || ok=false
check "studio/well-known" "http://127.0.0.1:3007/.well-known/mcp.json" || ok=false

if $ok; then
  echo ""
  echo "=== Librebase staging v${LIBREBASE_VERSION} healthy ==="
  echo "  Studio:   http://127.0.0.1:3007 (https://stage.librebase.xyz)"
  echo "  Admin:    http://127.0.0.1:54331 (internal only)"
else
  echo ""
  echo "=== DEPLOY FAILED ===" >&2
  docker compose -f docker-compose.staging.yml logs --tail=50
  exit 1
fi
