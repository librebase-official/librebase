#!/usr/bin/env bash
# Standalone compile of li_rt_container.c for local dev / ABI smoke.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/runtime/li_rt_container.c"
OUT="${1:-$ROOT/runtime/libli_rt_container.a}"
CC="${CC:-cc}"
CFLAGS=(-std=c11 -Wall -Wextra -fPIC -D_GNU_SOURCE -I"$ROOT/runtime")
if pkg-config --exists libseccomp 2>/dev/null; then
  CFLAGS+=(-DHAVE_LIBSECCOMP $(pkg-config --cflags libseccomp))
  LDFLAGS=($(pkg-config --libs libseccomp))
else
  LDFLAGS=()
fi
OBJ="${OUT%.a}.o"
"$CC" "${CFLAGS[@]}" -c "$SRC" -o "$OBJ"
rm -f "$OUT"
ar rcs "$OUT" "$OBJ"
echo "built: $OUT"
