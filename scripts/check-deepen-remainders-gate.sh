#!/usr/bin/env bash
# Deepen remainders gate — run from librebase repo root.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

TRACKER="$ROOT/docs/sdd/specs/parity-roadmap-v2/DEEPEN.json"
test -f "$TRACKER" || { echo "check-deepen-remainders-gate: missing DEEPEN.json" >&2; exit 1; }

python3 - "$TRACKER" <<'PY'
import json, sys
from pathlib import Path
p = Path(sys.argv[1])
data = json.loads(p.read_text(encoding="utf-8"))
status = data.get("status")
if status != "done":
    print(f"check-deepen-remainders-gate: status={status!r} want 'done'", file=sys.stderr)
    sys.exit(1)
slices = data.get("slices") or {}
# Remainders must not still say open-shaped stubs without resolution.
blocked = []
sig = slices.get("storage_sigv4", "")
if sig in ("done_shaped_mvp", "todo", "pending", ""):
    blocked.append(f"storage_sigv4={sig!r} (need deepen or honest oos)")
cdn = slices.get("cdn_image", "")
if cdn in ("passthrough_stub", "todo", "pending", ""):
    blocked.append(f"cdn_image={cdn!r} (need lean transform or oos)")
smtp = slices.get("auth_smtp", "missing")
if smtp in ("missing", "todo", "pending", ""):
    blocked.append(f"auth_smtp={smtp!r}")
pw = slices.get("playwright_browser", "")
if pw in ("todo", "pending", ""):
    blocked.append(f"playwright_browser={pw!r}")
if blocked:
    print("check-deepen-remainders-gate: unresolved slices:", file=sys.stderr)
    for b in blocked:
        print(f"  - {b}", file=sys.stderr)
    sys.exit(1)
print("check-deepen-remainders-gate: DEEPEN.json OK")
PY

test -f "$ROOT/data/goal-directed-sprints/wp-supabase-parity-deepen-remainders.md" \
  || { echo "check-deepen-remainders-gate: missing sprint goal file" >&2; exit 1; }

if [[ -f "$ROOT/scripts/e2e_deepen_phase1.py" ]]; then
  if [[ -z "${LIS_ROOT:-}" ]]; then
    if [[ -d /workspace/lis ]]; then export LIS_ROOT=/workspace/lis;
    elif [[ -d "$ROOT/../li/lis" ]]; then export LIS_ROOT="$ROOT/../li/lis";
    elif [[ -d "$ROOT/../lis" ]]; then export LIS_ROOT="$ROOT/../lis"; fi
  fi
  python3 "$ROOT/scripts/e2e_deepen_phase1.py" || {
    echo "check-deepen-remainders-gate: lean e2e failed" >&2
    exit 1
  }
fi

echo "check-deepen-remainders-gate: PASS"
