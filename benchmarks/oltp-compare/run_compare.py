#!/usr/bin/env python3
"""Librebase OLTP compare: lidb vs Postgres, with and without indexes.

Honesty
-------
- Reports measured P50/P95 only — never invents ratios without a Postgres URL.
- Prefer in-process EmbeddedSession (avoids exec-json subprocess masking index gains).
- Falls back to subprocess exec-json if liorm session unavailable.
- lidb indexed path requires CREATE INDEX (feat/wave-b-create-index+).
- Do not claim "as fast as Supabase" until CI publishes green rows.

Env
---
  LIDB_ROOT / LIDB_EMBED  — lidb checkout or embed binary
  POSTGRES_URL            — optional; enables Postgres compare
  BENCH_ROWS / BENCH_WARMUP / BENCH_MEASURE
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


def find_lidb_root() -> Path:
    return Path(
        os.environ.get(
            "LIDB_ROOT",
            r"C:\Users\Julian\Documents\Programming\li\lidb",
        )
    )


def find_embed() -> Path | None:
    override = os.environ.get("LIDB_EMBED", "").strip()
    if override and Path(override).is_file():
        return Path(override)
    root = find_lidb_root()
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


def try_session(data: Path):
    root = find_lidb_root()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    try:
        from liorm.embed_engine import EmbeddedSession, reset_session_for_tests  # type: ignore
    except Exception:
        return None
    reset_session_for_tests()
    os.environ.setdefault("LIDB_ROOT", str(root))
    embed = find_embed()
    if embed:
        os.environ["LIDB_EMBED"] = str(embed)
    session = EmbeddedSession(data)
    if not session.open_and_migrate():
        return None
    return session


def embed_exec(embed: Path, data: Path, sql: str, params: list[str] | None = None) -> list:
    proc = subprocess.run(
        [str(embed), "exec-json", str(data), sql],
        input=json.dumps(params or []),
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "exec-json failed")
    payload = json.loads(proc.stdout or '{"rows":[],"affected":0}')
    return list(payload.get("rows") or [])


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
        data.mkdir(parents=True, exist_ok=True)
        session = try_session(data)
        mode = "in_process" if session is not None else "subprocess_exec_json"

        def exec_sql(sql: str, params: list[str] | None = None) -> list:
            if session is not None:
                return session.exec_parameterized(sql, params or [])
            return embed_exec(embed, data, sql, params)

        if session is None:
            subprocess.run(
                [str(embed), "migrate", str(data)],
                check=True,
                capture_output=True,
                text=True,
            )

        exec_sql(
            "CREATE TABLE IF NOT EXISTS bench_items (id uuid, name text, owner_id uuid)"
        )
        target = f"lookup-{rows // 2}"
        for i in range(rows):
            exec_sql(
                "INSERT INTO bench_items (id, name, owner_id) VALUES (?, ?, ?)",
                [str(uuid.uuid4()), f"lookup-{i}", str(uuid.uuid4())],
            )

        def lidb_lookup() -> None:
            out = exec_sql(
                "SELECT id, name FROM bench_items WHERE name = ?",
                [target],
            )
            if not out:
                raise RuntimeError("lidb lookup miss")

        no_idx = time_fn(lidb_lookup, warmup=warmup, measure=measure)
        indexed_ok = True
        try:
            exec_sql(
                "CREATE INDEX IF NOT EXISTS idx_bench_items_name ON bench_items (name)"
            )
        except Exception:
            indexed_ok = False

        with_idx = (
            time_fn(lidb_lookup, warmup=warmup, measure=measure) if indexed_ok else None
        )

        scenarios: list[dict] = [
            {
                "engine": "lidb",
                "scenario": "point_lookup_no_index",
                "index": False,
                "status": "measured",
                **no_idx,
            }
        ]
        if with_idx is not None:
            row = {
                "engine": "lidb",
                "scenario": "point_lookup_with_index",
                "index": True,
                "status": "measured",
                **with_idx,
            }
            if no_idx["p95_ms"] > 0:
                row["speedup_vs_no_index_p95"] = round(
                    no_idx["p95_ms"] / with_idx["p95_ms"], 4
                )
            scenarios.append(row)
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

        if session is not None:
            session.close()

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
                cur.execute("CREATE INDEX idx_bench_items_name ON bench_items (name)")
                pg.commit()
                cur.execute("ANALYZE bench_items")
                pg.commit()
                pg_yes = time_fn(pg_lookup, warmup=warmup, measure=measure)
                pg_idx = {
                    "engine": "postgres",
                    "scenario": "point_lookup_with_index",
                    "index": True,
                    "status": "measured",
                    **pg_yes,
                }
                if pg_no["p95_ms"] > 0:
                    pg_idx["speedup_vs_no_index_p95"] = round(
                        pg_no["p95_ms"] / pg_yes["p95_ms"], 4
                    )
                scenarios.append(pg_idx)
                cur.close()
            finally:
                pg.close()

    by_key = {
        (s["engine"], s["index"]): s for s in scenarios if s["status"] == "measured"
    }
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
        "lidb_mode": mode,
        "embed": str(embed),
        "lidb_pin": "e9f8570",
        "postgres": bool(
            os.environ.get("POSTGRES_URL") or os.environ.get("DATABASE_URL")
        ),
        "honesty": (
            "Aims only until CI green. Prefer in-process EmbeddedSession so index gains "
            "are not masked by exec-json spawn. lidb index = in-memory hash/map — not "
            "B-tree / Postgres parity."
        ),
        "scenarios": scenarios,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rows", type=int, default=int(os.environ.get("BENCH_ROWS", "5000")))
    ap.add_argument("--warmup", type=int, default=int(os.environ.get("BENCH_WARMUP", "20")))
    ap.add_argument(
        "--measure", type=int, default=int(os.environ.get("BENCH_MEASURE", "100"))
    )
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
    print(f"wrote {args.json_out} mode={payload['lidb_mode']}")
    for s in payload["scenarios"]:
        print(
            f"  {s['engine']:8} {s['scenario']:28} "
            f"p95={s.get('p95_ms')} status={s['status']} "
            f"idx_speedup={s.get('speedup_vs_no_index_p95')} "
            f"vs_pg={s.get('ratio_vs_postgres_p95')}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
