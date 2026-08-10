#!/usr/bin/env bash
# Librebase full test suite — unit + integration.
#
# Usage:
#   bash scripts/run-tests.sh            # unit/integration (no live stack)
#   bash scripts/run-tests.sh --e2e      # also run the big MCP→todo-app E2E (needs lis+lidb)
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO"

echo "==> Python unit tests (parity runner, lidb engine, admin-api)"
python3 -m unittest discover -s tests -p "test_*.py"

echo "==> Admin API smoke (hosts + budget)"
python3 admin-api/scripts/smoke_admin.py

echo "==> SDK unit tests"
(cd packages/sdk && npm install --no-audit --no-fund >/dev/null 2>&1 && npm test)

echo "==> MCP unit + smoke + live e2e"
(cd packages/mcp && npm install --no-audit --no-fund >/dev/null 2>&1 && npm test)

echo "==> Studio unit tests + typecheck"
(cd data-studio-ui && npm install --no-audit --no-fund >/dev/null 2>&1 && npx tsc --noEmit && npm test)

echo "==> Todo app unit tests"
(cd apps/todo-app && npm install --no-audit --no-fund >/dev/null 2>&1 && node test/unit.mjs)

if [[ "${1:-}" == "--e2e" ]]; then
  echo "==> Big E2E: MCP provision → migration → todo app (SDK + HTTP)"
  node tests/e2e/todo-app-e2e.mjs
fi

echo "All tests passed."
