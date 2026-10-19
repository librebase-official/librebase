#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/apps/todo-app"
npm install
LIS_ROOT="${LIS_ROOT:-$ROOT/../lis}" node test/e2e.mjs
if [ -d "$ROOT/../lis" ] && [ -d "$ROOT/../lidb" ]; then
  node "$ROOT/tests/e2e/todo-app-e2e.mjs"
else
  echo "Skipping tests/e2e/todo-app-e2e.mjs (lis/lidb not present)"
fi
