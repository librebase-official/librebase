#!/usr/bin/env bash
# Security checklist for licontainer deployment (pure Li).
set -euo pipefail

PASS=0
FAIL=0

check() {
  if eval "$2"; then
    echo "[PASS] $1"
    PASS=$((PASS + 1))
  else
    echo "[FAIL] $1"
    FAIL=$((FAIL + 1))
  fi
}

check "pure Li policy doc" \
  "test -f licontainer/PURE-LI-POLICY.md"

check "no Rust in licontainer" \
  "! find licontainer -name '*.rs' | grep -q ."

check "no C in licontainer" \
  "! find licontainer -name '*.c' | grep -q ."

check "container seam in Li" \
  "test -f licontainer/packages/li-container/src/seam.li"

check "seccomp extern declared" \
  "grep -q container_seccomp_apply_i licontainer/packages/li-container/src/seam.li"

check "RFC for lic upstream" \
  "test -f docs/rfc-container-trusted-surface.md"

echo "---"
echo "Passed: $PASS  Failed: $FAIL"
exit $(( FAIL > 0 ? 1 : 0 ))
