#!/bin/sh
set -e

DATA_DIR="${LI_DATA_DIR:-/data}"
API_PORT="${LIBREBASE_API_PORT:-54320}"
PG_PORT="${LIBREBASE_PG_PORT:-54322}"
MODE="${LIDB_RUNTIME_MODE:-dev}"

mkdir -p "$DATA_DIR"

echo "librebase lidb-runtime starting (LIDB_RUNTIME_MODE=${MODE}) app=${APP_NAME:-default}"

# Production: persistent LiDB supervisor (preferred)
if [ -f /opt/librebase/scripts/lidb_supervisor.py ] && command -v lidb-engine >/dev/null 2>&1; then
  echo "PRODUCTION: LiDB supervisor — persistent SQL engine"
  exec python3 /opt/librebase/scripts/lidb_supervisor.py \
    --data-dir "$DATA_DIR" \
    --api-port "$API_PORT" \
    --app-name "${APP_NAME:-default}"
fi

# Fallback: librebase_api.py with lidb-engine backing
if command -v lidb-engine >/dev/null 2>&1; then
  echo "FALLBACK: librebase_api.py with lidb-engine"
  exec python3 /opt/librebase/scripts/librebase_api.py \
    --data-dir "$DATA_DIR" \
    --api-port "$API_PORT" \
    --postgres-port "$PG_PORT"
fi

# lis db start if available
if [ -n "$LIDB_ROOT" ] && [ -d "$LIDB_ROOT" ] && command -v lis >/dev/null 2>&1; then
  echo "production runtime: lis db start (LIDB_ROOT=$LIDB_ROOT)"
  export LI_DATA_DIR="$DATA_DIR"
  exec lis db start
fi

# Dev stub
echo "DEV MODE — file-backed stub (no lidb-engine)"
exec python3 /opt/librebase/scripts/dev_runtime_stub.py \
  --data-dir "$DATA_DIR" \
  --api-port "$API_PORT" \
  --postgres-port "$PG_PORT"
