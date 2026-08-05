#!/usr/bin/env python3
"""Soft gate for HTTP REST compare artifacts (P3).

Unlike check_gate.py (SQL):
  - skipped=true → exit 0 (soft-skip honesty when LIS/PostgREST unavailable)
  - ratio breach → WARN + exit 0 unless HTTP_SOFT_FAIL=1

Usage:
  python benchmarks/oltp-compare/check_http_gate.py [path/to/http-latest.json]
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DEFAULT_JSON = REPO / "benchmarks" / "oltp-compare" / "results" / "http-latest.json"

SOFT_SCENARIOS = ("rest_get_eq_name", "rest_post_insert")


def _ratio_max() -> float:
    return float(os.environ.get("HTTP_RATIO_MAX", "1.2"))


def _soft_fail() -> bool:
    return os.environ.get("HTTP_SOFT_FAIL", "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def check(payload: dict) -> int:
    errors: list[str] = []
    warnings: list[str] = []
    hard_max = _ratio_max()

    if payload.get("suite") and payload.get("suite") != "librebase-http-rest-compare":
        warnings.append(f"unexpected suite={payload.get('suite')!r}")

    if payload.get("skipped"):
        print(
            f"HTTP GATE: SKIP ({payload.get('skip_reason', 'no reason')}) — exit 0",
            file=sys.stderr,
        )
        return 0

    if not payload.get("lis_rest") or not payload.get("postgrest"):
        # Measured path should have both; treat as soft skip
        print(
            "HTTP GATE: SKIP (lis_rest/postgrest false without skipped flag) — exit 0",
            file=sys.stderr,
        )
        return 0

    scenarios = payload.get("scenarios") or []
    by_id = {
        (s.get("engine"), s.get("scenario")): s
        for s in scenarios
        if isinstance(s, dict)
    }

    print(
        f"http_gate: threshold={hard_max} pin={payload.get('lis_pin')} "
        f"soft_fail={_soft_fail()}"
    )
    print(f"{'engine':10} {'scenario':20} {'status':12} {'p95':>10} {'ratio':>8}")

    for s in scenarios:
        eng = s.get("engine", "?")
        sid = s.get("scenario", "?")
        status = s.get("status", "?")
        p95 = s.get("p95_ms")
        ratio = s.get("ratio_vs_postgrest_p95")
        p95_s = f"{p95:.4f}" if isinstance(p95, (int, float)) else "-"
        ratio_s = f"{ratio:.4f}" if isinstance(ratio, (int, float)) else "-"
        print(f"{eng:10} {sid:20} {status:12} {p95_s:>10} {ratio_s:>8}")

    soft = payload.get("soft_gate") or {}
    if soft.get("breached"):
        msg = (
            f"http_rest_p95: max_ratio={soft.get('max_ratio_vs_postgrest_p95')} "
            f"> {hard_max} (HTTP_RATIO_MAX)"
        )
        if _soft_fail():
            errors.append(msg)
        else:
            warnings.append(f"soft: {msg}")

    for sid in SOFT_SCENARIOS:
        row = by_id.get(("lis", sid))
        if row is None:
            warnings.append(f"soft: missing lis scenario {sid}")
            continue
        if row.get("status") != "measured":
            warnings.append(f"soft: {sid} status={row.get('status')!r}")
            continue
        ratio = row.get("ratio_vs_postgrest_p95")
        if ratio is None:
            warnings.append(f"soft: {sid} missing ratio_vs_postgrest_p95")
            continue
        if float(ratio) > hard_max:
            msg = f"{sid}: ratio_vs_postgrest_p95={ratio} > {hard_max}"
            if _soft_fail():
                errors.append(msg)
            else:
                warnings.append(f"soft: {msg}")

    for w in warnings:
        print(f"WARN: {w}", file=sys.stderr)
    for e in errors:
        print(f"FAIL: {e}", file=sys.stderr)

    if errors:
        print("HTTP GATE: FAIL", file=sys.stderr)
        return 1
    if warnings:
        print("HTTP GATE: WARN (soft — exit 0)")
        return 0
    print("HTTP GATE: PASS")
    return 0


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_JSON
    if not path.is_file():
        # Missing artifact → soft-skip for optional HTTP job
        print(f"HTTP GATE: SKIP (missing artifact {path}) — exit 0", file=sys.stderr)
        return 0
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"WARN: cannot parse {path}: {exc} — soft exit 0", file=sys.stderr)
        return 0
    if not isinstance(payload, dict):
        print("WARN: JSON root must be an object — soft exit 0", file=sys.stderr)
        return 0
    return check(payload)


if __name__ == "__main__":
    raise SystemExit(main())
