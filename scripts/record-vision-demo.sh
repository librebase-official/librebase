#!/usr/bin/env bash
# Prepare the Librebase vision demo for recording: health-check the three
# backends, seed the postgrest-js test data, and print the capture guide.
# Does not record video — prints macOS / QuickTime / ffmpeg hints.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FULLSTACK="$REPO_ROOT/benchmarks/full-stack"
SEED="$FULLSTACK/supalite/seed-rest.mjs"
RESULTS="$FULLSTACK/results"

# External stack locations (override via env).
FULL_SB_DIR="${FULL_SB_DIR:-/Users/julian/Documents/full-sb}"
LIS_DIR="${LIS_DIR:-/Users/julian/Documents/coding-projects/li-langverse-gitlab/li-langverse/lis}"

# Base URLs of the three backends under test.
LIS_URL="${LIS_URL:-http://127.0.0.1:54325}"
SUPALITE_URL="${SUPALITE_URL:-http://127.0.0.1:54321}"
FULL_URL="${FULL_URL:-http://127.0.0.1:8000}"

echo "==> Librebase vision demo prep"
echo "    repo: $REPO_ROOT"
echo "    script: docs/demo/librebase-vision-video-script.md"
echo "    storyboard: docs/demo/demo-storyboard.html"

if ! command -v node >/dev/null 2>&1; then
  echo "error: node required for seed-rest.mjs" >&2
  exit 1
fi

probe() {
  local code
  code="$(curl -s -o /dev/null -w '%{http_code}' --max-time 3 "$1" 2>/dev/null)" || code="000"
  printf '%s' "$code"
}
seed() {
  local rc=0
  node "$SEED" "$1" anon || rc=$?
  echo "    exit=$rc"
  return 0
}

echo ""
echo "==> backend health (000 = down)"
LB_CODE="$(probe "$LIS_URL/health")"
echo "    Librebase (lis)      $LIS_URL          -> $LB_CODE"
echo "    Supabase full (Kong) $FULL_URL         -> $(probe "$FULL_URL")"
echo "    Supalite (SQLite)    $SUPALITE_URL     -> $(probe "$SUPALITE_URL/rest/v1/")"

echo ""
echo "==> seed postgrest-js test data (Librebase + Supalite)"
if [ "$LB_CODE" != "000" ]; then
  seed "$LIS_URL"
else
  echo "    skip: Librebase not up (start lis, e.g. from $LIS_DIR)"
  echo "      LI_JWT_SECRET=change-me nohup python routes/registry/server.py --host 127.0.0.1 --port 54325 &"
fi
if [ "$(probe "$SUPALITE_URL/rest/v1/")" != "000" ]; then
  seed "$SUPALITE_URL"
else
  echo "    skip: Supalite not up (podman compose up in $SUPALITE_DIR)"
fi
echo "    note: lis creates the test tables implicitly on insert; Supalite needs"
echo "          those tables in its own schemas/schema.sql (postgrest-js schema is"
echo "          Postgres-typed — see postgrest-js-suite/README.md §Run)."

echo ""
echo "==> full-stack Supabase seed (if re-recording the suite beat)"
echo "    psql into the stack db and load the postgrest-js schema + seed:"
echo "      cd $FULL_SB_DIR && podman compose exec -T supabase-db psql -U postgres -d postgres < /tmp/pgtest-schema.sql"
echo "    results live in $RESULTS/"

echo ""
echo "==> Recording guide"
echo "    Beats: docs/demo/librebase-vision-video-script.md"
echo "    Storyboard: docs/demo/demo-storyboard.html (clickable, opens local files)"
echo ""
echo "    Beat 2 (footprint) commands to capture:"
echo "      podman images && podman stats --no-stream"
echo ""
echo "    Beat 4 (compat) suite runs:"
echo "      REST_URL=$LIS_URL/rest/v1 SEED=1 $FULLSTACK/postgrest-js-suite/run-suite.sh -u"
echo "      REST_URL=$FULL_URL/rest/v1 ANON_KEY=<anon from supabase_auth_admin> $FULLSTACK/postgrest-js-suite/run-suite.sh -u"
echo ""
echo "    macOS capture (pick one):"
echo "      • QuickTime Player -> File -> New Screen Recording"
if command -v ffmpeg >/dev/null 2>&1; then
  echo "      • ffmpeg (list displays): ffmpeg -f avfoundation -list_devices true -i \"\""
  echo "      • ffmpeg example (screen index may differ):"
  echo "        ffmpeg -f avfoundation -framerate 30 -capture_cursor 1 -i \"1:none\" -pix_fmt yuv420p ~/Desktop/librebase-vision-demo.mp4"
else
  echo "      • ffmpeg: not installed (brew install ffmpeg for CLI capture)"
fi
echo ""
echo "    Output: docs/demo/librebase-vision-benchmark.mp4 (ffmpeg, 1080p)"
