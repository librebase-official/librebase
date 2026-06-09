#!/usr/bin/env bash
# Build Li Container Engine workspace (Li-only).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WS="$ROOT/packages/li.toml"
LIC="${LIC:-${LIC_ROOT:-}/bin/lic}"
if [[ ! -x "$LIC" ]]; then
  if command -v lic >/dev/null 2>&1; then
    LIC="$(command -v lic)"
  else
    echo "error: set LIC_ROOT or put lic on PATH" >&2
    exit 1
  fi
fi
members=(li-container li-container-run li-containerd li-container-cli li-container-img li-container-cri)
for m in "${members[@]}"; do
  smoke="$ROOT/packages/$m/li-tests/smoke/builds.li"
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
done
echo "licontainer Li build: ok"
