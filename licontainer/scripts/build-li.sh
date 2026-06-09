#!/usr/bin/env bash
# Build Li Container Engine workspace (Li-only).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LIC="${LIC:-}"
if [[ -z "$LIC" && -n "${LIC_ROOT:-}" ]]; then
  if [[ -x "${LIC_ROOT}/bin/lic" ]]; then
    LIC="${LIC_ROOT}/bin/lic"
  elif [[ -f "${LIC_ROOT}/scripts/resolve-lic.sh" ]]; then
    LIC="$("${LIC_ROOT}/scripts/resolve-lic.sh")"
  fi
fi
if [[ -z "$LIC" ]] && command -v lic >/dev/null 2>&1; then
  LIC="$(command -v lic)"
fi
if [[ -z "$LIC" || ! -x "$LIC" ]]; then
  echo "error: set LIC_ROOT or put lic on PATH (use lic/scripts/resolve-lic.sh)" >&2
  exit 1
fi
members=(li-container li-container-run li-containerd li-container-cli li-container-img li-container-cri)
for m in "${members[@]}"; do
  smoke="$ROOT/packages/$m/li-tests/smoke/builds.li"
  integration="$ROOT/packages/$m/li-tests/integration"
  main="$ROOT/packages/$m/src/main.li"
  lib="$ROOT/packages/$m/src/lib.li"
  if [[ -f "$smoke" ]]; then
    echo "build: $m (smoke)"
    "$LIC" build --allow-open-vc --no-lean-verify "$smoke" -o /dev/null
  elif [[ -f "$main" ]]; then
    echo "build: $m (main)"
    "$LIC" build --allow-open-vc --no-lean-verify "$main" -o /dev/null
  elif [[ -f "$lib" ]]; then
    echo "build: $m (lib)"
    "$LIC" build --allow-open-vc --no-lean-verify "$lib" -o /dev/null
  fi
  if [[ -d "$integration" ]]; then
    for t in "$integration"/*.li; do
      [[ -f "$t" ]] || continue
      echo "build: $m (integration $(basename "$t"))"
      "$LIC" build --allow-open-vc --no-lean-verify "$t" -o /dev/null
    done
  fi
done

if [[ -f "$ROOT/packages/li-container-run/src/main.li" ]]; then
  mkdir -p "$ROOT/.build"
  echo "build: lirun binary"
  "$LIC" build --allow-open-vc --no-lean-verify "$ROOT/packages/li-container-run/src/main.li" -o "$ROOT/.build/lirun"
fi

echo "licontainer Li build: ok (pure Li — runtime impl in lic upstream)"
