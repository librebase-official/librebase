#!/usr/bin/env bash
# OSS compose smoke: stack up, admin health, Studio -> Admin, authenticated MCP.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
COMPOSE_DIR="$ROOT/deploy/compose"
cd "$COMPOSE_DIR"

if ! command -v docker >/dev/null 2>&1; then
  echo "compose-smoke.sh: docker not available, skipping" >&2
  exit 0
fi

DOCKER=(docker)
if ! docker info >/dev/null 2>&1; then
  if sudo docker info >/dev/null 2>&1; then
    DOCKER=(sudo docker)
  else
    echo "compose-smoke.sh: docker daemon not reachable" >&2
    exit 1
  fi
fi

docker_compose() {
  "${DOCKER[@]}" compose "$@"
}

ADMIN_JWT="$(openssl rand -hex 32)"
KMS_ROLE="$(openssl rand -hex 32)"
{
  echo "LIBREBASE_VERSION=0.1.38"
  echo "NEXT_PUBLIC_SITE_URL=http://127.0.0.1:3005"
  echo "LIBREBASE_CONSOLE_URL=http://127.0.0.1:3005"
  echo "LIBREBASE_ADMIN_JWT_SECRET=${ADMIN_JWT}"
  echo "LIBREBASE_KMS_SERVICE_ROLE=${KMS_ROLE}"
} > .env.smoke
trap 'docker_compose down -v >/dev/null 2>&1 || true; rm -f .env .env.smoke' EXIT

cp .env.smoke .env
docker_compose down -v >/dev/null 2>&1 || true
docker_compose build
docker_compose up -d

wait_url() {
  local url="$1"
  local i
  for i in $(seq 1 90); do
    if curl -sf --max-time 2 "$url" >/dev/null; then
      return 0
    fi
    sleep 2
  done
  echo "compose-smoke.sh: timeout waiting for $url" >&2
  docker_compose ps >&2 || true
  docker_compose logs --tail 80 >&2 || true
  return 1
}

wait_admin_health() {
  local i
  for i in $(seq 1 90); do
    if docker_compose exec -T librebase-admin wget -qO- --timeout=2 "http://127.0.0.1:54330/health" >/dev/null 2>&1; then
      return 0
    fi
    sleep 2
  done
  echo "compose-smoke.sh: timeout waiting for admin /health inside netns" >&2
  return 1
}

wait_admin_health
wait_url "http://127.0.0.1:3005/api/mcp"

SETUP_JSON="$(docker_compose exec -T librebase-admin python3 -c "
import json, urllib.request
body = json.dumps({
    'name': 'Smoke Org',
    'ownerEmail': 'smoke@example.com',
    'password': 'smoke-test-password-12',
}).encode()
req = urllib.request.Request(
    'http://127.0.0.1:54330/org/v1/setup',
    data=body,
    method='POST',
    headers={'Content-Type': 'application/json'},
)
print(urllib.request.urlopen(req, timeout=10).read().decode())
")"
MCP_KEY="$(python3 -c "import json,sys; print(json.load(sys.stdin)['mcpKey'])" <<<"$SETUP_JSON")"

docker_compose exec -T studio \
  wget -qO- --timeout=5 "http://127.0.0.1:54330/health" >/dev/null

MCP_RESP="$(curl -sf --max-time 20 -X POST "http://127.0.0.1:3005/api/mcp" \
  -H "Authorization: Bearer ${MCP_KEY}" \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"org_whoami","arguments":{}}}')"
python3 -c "import json,sys; r=json.load(sys.stdin); assert 'result' in r, r; t=r['result']['content'][0]['text']; assert 'orgId' in t" <<<"$MCP_RESP"

echo "compose-smoke.sh: OK"
