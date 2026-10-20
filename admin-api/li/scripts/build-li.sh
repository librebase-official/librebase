#!/usr/bin/env bash
# admin-api/li/scripts/build-li.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
LI_ROOT="$ROOT/admin-api/li"
OUT="$LI_ROOT/build"
mkdir -p "$OUT"
LIC_ROOT="${LIC_ROOT:-$ROOT/../lic}"

list_li_only() {
  echo "lic unavailable or unresolved at LIC_ROOT=$LIC_ROOT — syntax listing only"
  find "$LI_ROOT" -name '*.li' | sort
  exit 0
}

LIC="${LIC:-}"
if [[ -z "$LIC" && -n "${LIC_ROOT:-}" ]]; then
  if [[ -x "${LIC_ROOT}/bin/lic" ]]; then
    LIC="${LIC_ROOT}/bin/lic"
  elif [[ -x "${LIC_ROOT}/build-mac/compiler/lic/lic" ]]; then
    LIC="${LIC_ROOT}/build-mac/compiler/lic/lic"
  elif [[ -x "${LIC_ROOT}/build/compiler/lic/lic" ]]; then
    LIC="${LIC_ROOT}/build/compiler/lic/lic"
  elif [[ -f "${LIC_ROOT}/scripts/resolve-lic.sh" ]]; then
    LIC="$("${LIC_ROOT}/scripts/resolve-lic.sh" 2>/dev/null)" || true
  fi
fi
if [[ -z "$LIC" ]] && command -v lic >/dev/null 2>&1; then
  LIC="$(command -v lic)"
fi
if [[ -z "$LIC" || ! -x "$LIC" ]]; then
  list_li_only
fi

export LI_NATIVE_RT="${LI_NATIVE_RT:-1}"
if [[ -z "${LI_RT_LIB:-}" ]]; then
  for candidate in \
    "${LIC_ROOT}/build-mac/runtime/libli_rt.a" \
    "${LIC_ROOT}/build/runtime/libli_rt.a"; do
    if [[ -f "$candidate" ]]; then
      export LI_RT_LIB="$candidate"
      break
    fi
  done
fi
"$LIC" build "$LI_ROOT/src/admin_server.li" -o "$OUT/admin_server"
chmod +x "$OUT/admin_server"
echo "built $OUT/admin_server"
