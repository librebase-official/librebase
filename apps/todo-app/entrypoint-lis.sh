#!/usr/bin/env bash
# Start the Librebase lis backend (auth + REST + storage) on :54321.
# Pure-stdlib python — no lidb_embed, mock auth, in-memory REST store.
set -euo pipefail
export PYTHONPATH=/opt/lis
export LI_API_PORT="${LI_API_PORT:-54321}"
export LI_REGISTRY_PORT="${LI_API_PORT}"
export LI_JWT_SECRET="${LI_JWT_SECRET:-change-me}"
export LI_AUTH_BACKEND="${LI_AUTH_BACKEND:-mock}"
export LI_REGISTRY_MOCK="${LI_REGISTRY_MOCK:-1}"
export LI_DATA_DIR="${LI_DATA_DIR:-/data/lis}"
export LI_STORAGE_DIR="${LI_STORAGE_DIR:-/data/lis/storage}"

mkdir -p "$LI_DATA_DIR" "$LI_STORAGE_DIR"
exec python3 /opt/lis/routes/registry/server.py --host 0.0.0.0 --port "$LI_API_PORT"
