#!/usr/bin/env bash
# Security checklist for licontainer deployment.
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

check "daemon socket mode 0600" \
  "test \$(stat -c '%a' /run/licontainer/licontainerd.sock 2>/dev/null) = 600"

check "no privileged API in licontainerd" \
  "! grep -rq 'privileged' licontainer/licontainerd/src/ 2>/dev/null || grep -q 'No.*privileged' docs/licontainer.md"

check "seccomp module present" \
  "test -f licontainer/lirun/src/seccomp.rs"

check "cgroup pids.max default" \
  "grep -q 'pids.max' licontainer/lirun/src/bundle.rs"

check "entitlement TODO on pull/create" \
  "grep -q 'check_entitlement' licontainer/licontainer-proto/src/lib.rs"

echo "---"
echo "Passed: $PASS  Failed: $FAIL"
exit $(( FAIL > 0 ? 1 : 0 ))
