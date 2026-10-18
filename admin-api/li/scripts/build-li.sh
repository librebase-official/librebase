#!/usr/bin/env bash
# admin-api/li/scripts/build-li.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
LI_ROOT="$ROOT/admin-api/li"
OUT="$LI_ROOT/build"
mkdir -p "$OUT"
LIC_ROOT="${LIC_ROOT:-$ROOT/../lic}"
if [[ ! -x "$LIC_ROOT/scripts/resolve-lic.sh" && ! -x "$LIC_ROOT/build/lic" && ! -x "$LIC_ROOT/build-mac/lic" ]]; then
  echo "lic unavailable at LIC_ROOT=$LIC_ROOT — syntax listing only"
  find "$LI_ROOT" -name '*.li' | sort
  exit 0
fi
export LI_NATIVE_RT="${LI_NATIVE_RT:-1}"
# Prefer packaged build; fall back to compiling main entry
if command -v lic >/dev/null 2>&1; then
  lic build "$LI_ROOT/src/admin_server.li" -o "$OUT/admin_server"
else
  echo "lic not on PATH; set LIC_ROOT and ensure resolve-lic.sh"
  exit 1
fi
chmod +x "$OUT/admin_server"
echo "built $OUT/admin_server"
