#!/usr/bin/env bash
# OSS compose smoke: bridge network, setup, MCP, and kms force-recreate resilience.
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

restart_dockerd() {
  echo "compose-smoke.sh: restarting dockerd (intermittent bridge workaround)" >&2
  if command -v systemctl >/dev/null 2>&1; then
    sudo systemctl restart docker 2>/dev/null || true
  fi
  if ! "${DOCKER[@]}" info >/dev/null 2>&1; then
    sudo pkill -x dockerd 2>/dev/null || true
    sleep 1
    sudo dockerd >/tmp/dockerd-smoke.log 2>&1 &
    sleep 8
  fi
  if ! "${DOCKER[@]}" info >/dev/null 2>&1; then
    echo "compose-smoke.sh: dockerd still unreachable after restart" >&2
    return 1
  fi
}

studio_to_admin_health() {
  docker_compose exec -T studio node -e "
fetch('http://librebase-admin:54330/health', { signal: AbortSignal.timeout(5000) })
  .then((r) => r.text())
  .then((t) => { if (!t.includes('ok')) throw new Error(t); })
  .catch((e) => { console.error(e); process.exit(1); });
" >/dev/null 2>&1
}

verify_bridge_with_retry() {
  if studio_to_admin_health; then
    return 0
  fi
  restart_dockerd || return 1
  cp .env.smoke .env
  docker_compose down -v >/dev/null 2>&1 || true
  docker_compose up -d
  wait_stack_ready || return 1
  if studio_to_admin_health; then
    return 0
  fi
  echo "compose-smoke.sh: studio cannot reach librebase-admin:54330 after dockerd restart" >&2
  return 1
}

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

wait_stack_ready() {
  local i
  for i in $(seq 1 120); do
    if docker_compose ps --status running 2>/dev/null | grep -q studio; then
      if docker_compose exec -T librebase-admin wget -qO- --timeout=2 "http://127.0.0.1:54330/health" >/dev/null 2>&1 \
        && curl -sf --max-time 2 "http://127.0.0.1:3005/api/mcp" >/dev/null 2>&1; then
        return 0
      fi
    fi
    sleep 2
  done
  echo "compose-smoke.sh: timeout waiting for stack health" >&2
  return 1
}

run_org_setup() {
  docker_compose exec -T librebase-admin python3 -c "
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
"
}

mcp_org_whoami() {
  local mcp_key="$1"
  curl -sf --max-time 25 -X POST "http://127.0.0.1:3005/api/mcp" \
    -H "Authorization: Bearer ${mcp_key}" \
    -H 'Content-Type: application/json' \
    -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"org_whoami","arguments":{}}}'
}

assert_mcp_whoami() {
  local resp="$1"
  python3 -c "import json,sys; r=json.load(sys.stdin); assert 'result' in r, r; t=r['result']['content'][0]['text']; assert 'orgId' in t" <<<"$resp"
}

ADMIN_JWT="$(openssl rand -hex 32)"
KMS_ROLE="$(openssl rand -hex 32)"
LIBREBASE_VERSION="$(cat "${ROOT}/VERSION")"
{
  echo "LIBREBASE_VERSION=${LIBREBASE_VERSION}"
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
wait_stack_ready
verify_bridge_with_retry

SETUP_JSON="$(run_org_setup)"
MCP_KEY="$(python3 -c "import json,sys; print(json.load(sys.stdin)['mcpKey'])" <<<"$SETUP_JSON")"

MCP_RESP="$(mcp_org_whoami "$MCP_KEY")"
assert_mcp_whoami "$MCP_RESP"

echo "compose-smoke.sh: forcing kms recreate"
docker_compose up -d --force-recreate kms
docker_compose up -d
wait_stack_ready
verify_bridge_with_retry

MCP_RESP="$(mcp_org_whoami "$MCP_KEY")"
assert_mcp_whoami "$MCP_RESP"

echo "compose-smoke.sh: OK"
