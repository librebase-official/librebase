#!/usr/bin/env bash
# Run the official @supabase/postgrest-js test suite against a backend.
#
# Tiered methodology (fair comparison — see README.md):
#   - in-memory tier: lis memory store vs in-memory SQLite
#   - on-disk tier:  lis + lidb vs SQLite(file) vs Supabase full (Postgres)
#
# Usage:
#   REST_URL=http://127.0.0.1:54325/rest/v1 SEED=1 ./run-suite.sh [jest-args]
#
#   REST_URL   Base /rest/v1 URL of the backend under test
#   ANON_KEY   apikey header value (Supabase full/Kong requires it)
#   SEED=1     load the postgrest-js test seed data first (REST inserts)
#   SUITE_DIR  where the postgrest-js checkout lives (default: /tmp/postgrest-js)
set -euo pipefail

REST_URL="${REST_URL:?set REST_URL, e.g. http://127.0.0.1:54325/rest/v1}"
ANON_KEY="${ANON_KEY:-}"
SUITE_DIR="${SUITE_DIR:-/tmp/postgrest-js}"
REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
SUITE_PKG="$SUITE_DIR/packages/core/postgrest-js"

if [ ! -d "$SUITE_PKG" ]; then
  echo ">> cloning supabase-js (postgrest-js suite) into $SUITE_DIR"
  git clone --depth 1 https://github.com/supabase/supabase-js.git "$SUITE_DIR"
  (cd "$SUITE_DIR" && pnpm install --filter postgrest-js... >/dev/null 2>&1)
fi

# Seed the test data via the Data API (backend-agnostic)
if [ "${SEED:-0}" = "1" ]; then
  echo ">> seeding postgrest-js test schema data via REST"
  # seed-rest.mjs takes the base API URL (supabase-js appends /rest/v1)
  SEED_BASE="${REST_URL%%/rest/v1*}"
  node "$REPO_ROOT/benchmarks/full-stack/supalite/seed-rest.mjs" "$SEED_BASE" "${ANON_KEY:-anon}"
fi

cd "$SUITE_PKG"
# Point the suite at the backend under test; inject apikey when Kong requires it
if [ -n "$ANON_KEY" ]; then
  export ANON_KEY
  SETUP='-i <rootDir>/test/setup-kong.ts'
else
  SETUP=''
fi

echo ">> running postgrest-js suite against $REST_URL"
REST_URL="$REST_URL" npx jest --runInBand $SETUP --testPathIgnorePatterns='test/v12/' "$@"
