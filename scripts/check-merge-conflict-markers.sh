#!/usr/bin/env bash
# Fail if git conflict markers are present in tracked source/docs paths.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if git grep -nE '(^<<<<<<<|^=======$|^>>>>>>>)' -- \
  ':!*.next/**' \
  ':!**/node_modules/**' \
  ':!pricing_validation.py' \
  ':!docs/demo/**' \
  ':!data-saas-admin/.next/**' \
  ; then
  echo "check-merge-conflict-markers.sh: unresolved merge conflict markers found" >&2
  exit 1
fi

echo "check-merge-conflict-markers.sh: OK"
