#!/usr/bin/env python3
"""Pass/fail gate for librebase OLTP compare JSON artifacts.

Hard gate (exit 1):
  - payload skipped / missing postgres
  - mode != embed_execjson (embed_inprocess is diagnostic-only)
  - lidb point_lookup_with_index missing, not measured, or index_unsupported
  - range_scan_name_prefix when index_impl is sorted_tree or btree (same rules)
  - ratio_vs_postgres_p95 > OLTP_RATIO_MAX (default 1.2)

Soft gate (warn; exit 1 only if OLTP_SOFT_FAIL=1):
  - point_insert / indexed_read_write_mix ratio_vs_postgres_p95 > OLTP_SOFT_RATIO_MAX
    (default 1.5)

Usage:
  python benchmarks/oltp-compare/check_gate.py [path/to/latest.json]
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DEFAULT_JSON = REPO / "benchmarks" / "oltp-compare" / "results" / "latest.json"

HARD_GATED_BASE = ("point_lookup_with_index",)
RANGE_SCAN = "range_scan_name_prefix"
INDEXED_IMPLS = frozenset(("sorted_tree", "btree"))
GATED_MODE = "embed_execjson"
SOFT_GATED = ("point_insert", "indexed_read_write_mix")


def _hard_gated(payload: dict) -> tuple[str, ...]:
    gated: list[str] = list(HARD_GATED_BASE)
    if payload.get("index_impl") in INDEXED_IMPLS:
        gated.append(RANGE_SCAN)
    return tuple(gated)


def _ratio_max() -> float:
    return float(os.environ.get("OLTP_RATIO_MAX", "1.2"))


def _soft_ratio_max() -> float:
    return float(os.environ.get("OLTP_SOFT_RATIO_MAX", "1.5"))


def _soft_fail() -> bool:
    return os.environ.get("OLTP_SOFT_FAIL", "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def check(payload: dict) -> int:
    errors: list[str] = []
    warnings: list[str] = []
    hard_max = _ratio_max()
    soft_max = _soft_ratio_max()
    hard_gated = _hard_gated(payload)

    if payload.get("skipped"):
        errors.append(
            f"skipped=true ({payload.get('skip_reason', 'no reason')}) — "
            "intentional CI runs must not skip"
        )

    if not payload.get("postgres"):
        errors.append("postgres=false — gate requires a Postgres head-to-head")

    mode = payload.get("mode") or payload.get("lidb_mode")
    if mode != GATED_MODE:
        errors.append(
            f"mode={mode!r} — CI hard gate requires {GATED_MODE!r} "
            "(embed_inprocess is diagnostic-only; unfair vs TCP Postgres)"
        )

    scenarios = payload.get("scenarios") or []
    by_id = {
        (s.get("engine"), s.get("scenario")): s
        for s in scenarios
        if isinstance(s, dict)
    }

    print(
        f"gate: mode={mode} pin={payload.get('lidb_pin')} "
        f"index_impl={payload.get('index_impl')} hard_gated={hard_gated} "
        f"hard_max={hard_max} soft_max={soft_max}"
    )
    print(
        f"{'engine':8} {'scenario':28} {'status':18} {'p95':>10} {'ratio':>8} {'class':10}"
    )

    for s in scenarios:
        eng = s.get("engine", "?")
        sid = s.get("scenario", "?")
        status = s.get("status", "?")
        p95 = s.get("p95_ms")
        ratio = s.get("ratio_vs_postgres_p95")
        gclass = s.get("gate_class", "")
        p95_s = f"{p95:.4f}" if isinstance(p95, (int, float)) else "-"
        ratio_s = f"{ratio:.4f}" if isinstance(ratio, (int, float)) else "-"
        print(f"{eng:8} {sid:28} {status:18} {p95_s:>10} {ratio_s:>8} {gclass:10}")

    for sid in hard_gated:
        row = by_id.get(("lidb", sid))
        if row is None:
            errors.append(f"missing lidb scenario {sid}")
            continue
        status = row.get("status")
        if status == "index_unsupported":
            errors.append(f"{sid}: index_unsupported (pin too old / no CREATE INDEX)")
            continue
        if status != "measured":
            errors.append(f"{sid}: status={status!r} (want measured)")
            continue
        ratio = row.get("ratio_vs_postgres_p95")
        if ratio is None:
            errors.append(f"{sid}: missing ratio_vs_postgres_p95")
            continue
        if float(ratio) > hard_max:
            errors.append(
                f"{sid}: ratio_vs_postgres_p95={ratio} > {hard_max} (OLTP_RATIO_MAX)"
            )

    for sid in SOFT_GATED:
        row = by_id.get(("lidb", sid))
        if row is None:
            warnings.append(f"soft: missing lidb scenario {sid} (not in this run)")
            continue
        status = row.get("status")
        if status == "index_unsupported":
            # mix needs index; treat as hard if present in payload
            if sid == "indexed_read_write_mix":
                errors.append(f"{sid}: index_unsupported")
            else:
                warnings.append(f"soft: {sid} index_unsupported")
            continue
        if status != "measured":
            warnings.append(f"soft: {sid} status={status!r}")
            continue
        ratio = row.get("ratio_vs_postgres_p95")
        if ratio is None:
            warnings.append(f"soft: {sid} missing ratio_vs_postgres_p95")
            continue
        if float(ratio) > soft_max:
            msg = (
                f"{sid}: ratio_vs_postgres_p95={ratio} > {soft_max} "
                f"(OLTP_SOFT_RATIO_MAX soft gate)"
            )
            if _soft_fail():
                errors.append(msg)
            else:
                warnings.append(f"soft: {msg}")

    for w in warnings:
        print(f"WARN: {w}", file=sys.stderr)
    for e in errors:
        print(f"FAIL: {e}", file=sys.stderr)

    if errors:
        print("GATE: FAIL", file=sys.stderr)
        return 1
    print("GATE: PASS")
    return 0


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_JSON
    if not path.is_file():
        print(f"FAIL: missing artifact {path}", file=sys.stderr)
        return 1
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"FAIL: cannot parse {path}: {exc}", file=sys.stderr)
        return 1
    if not isinstance(payload, dict):
        print("FAIL: JSON root must be an object", file=sys.stderr)
        return 1
    return check(payload)


if __name__ == "__main__":
    raise SystemExit(main())
