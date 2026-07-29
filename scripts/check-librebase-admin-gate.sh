#!/usr/bin/env bash
# Librebase Admin integration gate — run from librebase repo root.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

required=(
  data-studio-ui/lib/librebase-admin-client.ts
  data-studio-ui/lib/org-context.ts
  data-studio-ui/lib/entitlements.ts
  deploy/compose/docker-compose.yml
)
for f in "${required[@]}"; do
  test -f "$ROOT/$f" || { echo "check-librebase-admin-gate.sh: missing $f" >&2; exit 1; }
done

if command -v npm >/dev/null 2>&1; then
  (cd "$ROOT/data-studio-ui" && npm test -- --run 2>&1)
fi

echo "check-librebase-admin-gate.sh: PASS"
