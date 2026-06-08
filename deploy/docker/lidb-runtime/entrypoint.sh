#!/bin/sh
set -e

DATA_DIR="${LI_DATA_DIR:-/data}"
API_PORT="${LIBREBASE_API_PORT:-54320}"
PG_PORT="${LIBREBASE_PG_PORT:-54322}"
MODE="${LIDB_RUNTIME_MODE:-dev}"

mkdir -p "$DATA_DIR"

echo "librebase lidb-runtime starting (LIDB_RUNTIME_MODE=${MODE})"

if [ -n "$LIDB_ROOT" ] && [ -d "$LIDB_ROOT" ] && command -v lis >/dev/null 2>&1; then
  echo "production runtime: lis db start (LIDB_ROOT=$LIDB_ROOT)"
  export LI_DATA_DIR="$DATA_DIR"
  export LIBREBASE_API_PORT="$API_PORT"
  export LIBREBASE_PG_PORT="$PG_PORT"
  exec lis db start
fi

if [ "$MODE" = "dev" ]; then
  echo "DEV MODE — dev_runtime_stub (not production lidb)"
  exec python3 /opt/librebase/scripts/dev_runtime_stub.py \
    --data-dir "$DATA_DIR" \
    --api-port "$API_PORT" \
    --postgres-port "$PG_PORT"
fi

echo "ERROR: no LIDB_ROOT/lis and LIDB_RUNTIME_MODE is not dev"
exit 1
