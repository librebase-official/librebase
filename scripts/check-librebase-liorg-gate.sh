#!/usr/bin/env bash
# WP-5 librebase integration gate — run from librebase repo root.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

required=(
  data-studio-ui/lib/liorg-client.ts
  data-studio-ui/lib/org-context.ts
  data-studio-ui/lib/entitlements.ts
  deploy/compose/docker-compose.yml
)
for f in "${required[@]}"; do
  test -f "$ROOT/$f" || { echo "check-librebase-liorg-gate.sh: missing $f" >&2; exit 1; }
done

if command -v npm >/dev/null 2>&1; then
  (cd "$ROOT/data-studio-ui" && npm test -- --run 2>&1)
fi

LIORG_ROOT="${LIORG_ROOT:-../liorg}"
if [[ -x "$LIORG_ROOT/scripts/test-http-smoke.sh" ]]; then
  bash "$LIORG_ROOT/scripts/test-http-smoke.sh"
fi

echo "check-librebase-liorg-gate.sh: PASS"
