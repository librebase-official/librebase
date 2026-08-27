#!/usr/bin/env bash
# Sync admin.db from VPS #2 to the homelab engine.
# Run this periodically (e.g. cron every 5 min) or manually before checking the dashboard.
set -euo pipefail

VPS_HOST="${LIBREBASE_VPS2_HOST:-87.106.2.129}"
VPS_USER="${LIBREBASE_VPS2_USER:-root}"
REMOTE_DB="/opt/librebase-admin/data/admin.db"
LOCAL_DB="${1:-/home/s4il0r/saas-admin/data/admin.db}"

mkdir -p "$(dirname "$LOCAL_DB")"

echo "Syncing admin.db from $VPS_USER@$VPS_HOST:$REMOTE_DB → $LOCAL_DB"
scp "${VPS_USER}@${VPS_HOST}:${REMOTE_DB}" "${LOCAL_DB}"
echo "Done. $(stat -f%z "$LOCAL_DB" 2>/dev/null || stat -c%s "$LOCAL_DB") bytes"
