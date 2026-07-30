#!/usr/bin/env python3
"""Librebase OLTP compare: lidb vs Postgres, with and without indexes.

Honesty
-------
- Reports measured P50/P95 only — never invents ratios without a Postgres URL.
- lidb indexed path requires lidb_embed that supports CREATE INDEX (feat/wave-b-create-index+).
  If CREATE INDEX fails, the indexed lidb scenario is marked ``index_unsupported``.
- Postgres runs both seq-scan (no index) and btree-index lookups on the same row set.
- Do not claim "as fast as Supabase" from this script until CI publishes green rows.

Env
---
  LIDB_ROOT / LIDB_EMBED  — lidb checkout or embed binary
  POSTGRES_URL            — optional; enables Postgres compare
  BENCH_ROWS              — seed size (default 5000)
  BENCH_WARMUP / BENCH_MEASURE
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def p95_ms(samples: list[float]) -> float:
    if not samples:
        return 0.0
    ordered = sorted(samples)
    return ordered[max(0, int(round(0.95 * (len(ordered) - 1))))]


def timing_stats(samples: list[float]) -> dict:
    if not samples:
        return {"mean_ms": 0.0, "p50_ms": 0.0, "p95_ms": 0.0, "n": 0}
    return {
        "mean_ms": round(statistics.mean(samples), 4),
        "p50_ms": round(statistics.median(samples), 4),
        "p95_ms": round(p95_ms(samples), 4),
        "n": len(samples),
    }


def time_fn(fn, *, warmup: int, measure: int) -> dict:
    for _ in range(warmup):
        fn()
    samples: list[float] = []
    for _ in range(measure):
        t0 = time.perf_counter()
        fn()
        samples.append((time.perf_counter() - t0) * 1000.0)
    return timing_stats(samples)


def find_embed() -> Path | None:
    override = os.environ.get("LIDB_EMBED", "").strip()
    if override and Path(override).is_file():
        return Path(override)
    root = Path(os.environ.get("LIDB_ROOT", r"C:\Users\Julian\Documents\Programming\li\lidb"))
    for cand in (
        root / "build" / "smoke" / "Release" / "lidb_embed.exe",
        root / "build" / "smoke" / "lidb_embed.exe",
        root / "build" / "smoke" / "lidb_embed",
        root / "build" / "Release" / "lidb_embed.exe",
        root / "build" / "lidb_embed.exe",
        root / "build" / "lidb_embed",
    ):
        if cand.is_file():
            return cand
    return None


def embed_exec(embed: Path, data: Path, sql: str, params: list[str] | None = None) -> dict:
    proc = subprocess.run(
        [str(embed), "exec-json", str(data), sql],
        input=json.dumps(params or []),
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "exec-json failed")
    return json.loads(proc.stdout or '{"rows":[],"affected":0}')


def lidb_seed(embed: Path, data: Path, n: int) -> str:
    data.mkdir(parents=True, exist_ok=True)
    subprocess.run([str(embed), "migrate", str(data)], check=True, capture_output=True, text=True)
    # Prefer allowlisted CREATE TABLE shape (no PK/NOT NULL).
    embed_exec(
        embed,
        data,
        "CREATE TABLE IF NOT EXISTS bench_items (id uuid, name text, owner_id uuid)",
    )
    target = f"lookup-{n // 2}"
    for i in range(n):
        rid = str(uuid.uuid4())
        name = f"lookup-{i}"
        owner = str(uuid.uuid4())
        embed_exec(
            embed,
            data,
            "INSERT INTO bench_items (id, name, owner_id) VALUES (?, ?, ?)",
            [rid, name, owner],
        )
    return target


def lidb_try_index(embed: Path, data: Path) -> bool:
    try:
        embed_exec(
            embed,
            data,
            "CREATE INDEX IF NOT EXISTS idx_bench_items_name ON bench_items (name)",
        )
        return True
    except RuntimeError:
        return False


def pg_connect():
    url = os.environ.get("POSTGRES_URL") or os.environ.get("DATABASE_URL")
    if not url:
        return None
    try:
        import psycopg2  # type: ignore
    except ImportError:
        return None
    return psycopg2.connect(url)


def pg_prepare(conn, n: int) -> str:
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS bench_items")
    cur.execute(
        """
        CREATE TABLE bench_items (
            id UUID PRIMARY KEY,
            name TEXT NOT NULL,
            owner_id UUID NOT NULL
        )
        """
    )
    target = f"lookup-{n // 2}"
    for i in range(n):
        cur.execute(
            "INSERT INTO bench_items (id, name, owner_id) VALUES (%s, %s, %s)",
            (str(uuid.uuid4()), f"lookup-{i}", str(uuid.uuid4())),
        )
    conn.commit()
    cur.close()
    return target


def run(*, rows: int, warmup: int, measure: int) -> dict:
    embed = find_embed()
    if embed is None:
        raise RuntimeError("lidb_embed not found — set LIDB_EMBED or LIDB_ROOT")

    with tempfile.TemporaryDirectory(prefix="lb-oltp-") as tmp:
        data = Path(tmp) / "lidb"
        target = lidb_seed(embed, data, rows)

        def lidb_lookup() -> None:
            out = embed_exec(
                embed,
                data,
                "SELECT id, name FROM bench_items WHERE name = ?",
                [target],
            )
            if not out.get("rows"):
                raise RuntimeError("lidb lookup miss")

        no_idx = time_fn(lidb_lookup, warmup=warmup, measure=measure)
        indexed_ok = lidb_try_index(embed, data)
        with_idx = (
            time_fn(lidb_lookup, warmup=warmup, measure=measure)
            if indexed_ok
            else None
        )

        scenarios = [
            {
                "engine": "lidb",
                "scenario": "point_lookup_no_index",
                "index": False,
                "status": "measured",
                **no_idx,
            }
        ]
        if with_idx is not None:
            scenarios.append(
                {
                    "engine": "lidb",
                    "scenario": "point_lookup_with_index",
                    "index": True,
                    "status": "measured",
                    **with_idx,
                }
            )
        else:
            scenarios.append(
                {
                    "engine": "lidb",
                    "scenario": "point_lookup_with_index",
                    "index": True,
                    "status": "index_unsupported",
                    "mean_ms": None,
                    "p50_ms": None,
                    "p95_ms": None,
                    "n": 0,
                    "note": "CREATE INDEX not available in this lidb_embed build",
                }
            )

        pg = pg_connect()
        if pg:
            try:
                pg_target = pg_prepare(pg, rows)
                cur = pg.cursor()

                def pg_lookup() -> None:
                    cur.execute(
                        "SELECT id, name FROM bench_items WHERE name = %s",
                        (pg_target,),
                    )
                    if not cur.fetchone():
                        raise RuntimeError("postgres lookup miss")

                pg_no = time_fn(pg_lookup, warmup=warmup, measure=measure)
                scenarios.append(
                    {
                        "engine": "postgres",
                        "scenario": "point_lookup_no_index",
                        "index": False,
                        "status": "measured",
                        **pg_no,
                    }
                )
                cur.execute(
                    "CREATE INDEX idx_bench_items_name ON bench_items (name)"
                )
                pg.commit()
                # Force planner to consider index
                cur.execute("ANALYZE bench_items")
                pg.commit()
                pg_yes = time_fn(pg_lookup, warmup=warmup, measure=measure)
                scenarios.append(
                    {
                        "engine": "postgres",
                        "scenario": "point_lookup_with_index",
                        "index": True,
                        "status": "measured",
                        **pg_yes,
                    }
                )
                cur.close()
            finally:
                pg.close()

    # Ratios vs Postgres same index mode when both measured
    by_key = {(s["engine"], s["index"]): s for s in scenarios if s["status"] == "measured"}
    for s in scenarios:
        if s["engine"] != "lidb" or s["status"] != "measured":
            continue
        pg_row = by_key.get(("postgres", s["index"]))
        if pg_row and pg_row.get("p95_ms"):
            s["ratio_vs_postgres_p95"] = round(s["p95_ms"] / pg_row["p95_ms"], 4)

    return {
        "suite": "librebase-oltp-index-compare",
        "rows_seeded": rows,
        "warmup": warmup,
        "measure": measure,
        "embed": str(embed),
        "postgres": bool(os.environ.get("POSTGRES_URL") or os.environ.get("DATABASE_URL")),
        "honesty": (
            "Aims only until CI green. lidb index = in-memory map when CREATE INDEX supported; "
            "not B-tree / Postgres index parity. Indexes still skipped by SQL-file migrate unless "
            "allowlisted CREATE INDEX lands."
        ),
        "scenarios": scenarios,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rows", type=int, default=int(os.environ.get("BENCH_ROWS", "5000")))
    ap.add_argument("--warmup", type=int, default=int(os.environ.get("BENCH_WARMUP", "20")))
    ap.add_argument("--measure", type=int, default=int(os.environ.get("BENCH_MEASURE", "100")))
    ap.add_argument(
        "--json-out",
        type=Path,
        default=REPO / "benchmarks" / "oltp-compare" / "results" / "latest.json",
    )
    args = ap.parse_args()
    try:
        payload = run(rows=args.rows, warmup=args.warmup, measure=args.measure)
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {args.json_out}")
    for s in payload["scenarios"]:
        print(
            f"  {s['engine']:8} {s['scenario']:28} "
            f"p95={s.get('p95_ms')} status={s['status']} "
            f"ratio={s.get('ratio_vs_postgres_p95')}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
