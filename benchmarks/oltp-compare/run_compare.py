#!/usr/bin/env python3
"""Librebase OLTP compare: lidb vs Postgres (fairness modes + multi-scenario).

Honesty
-------
- Reports measured P50/P95 (and ops/sec where relevant) — never invents ratios
  without a Postgres URL.
- Modes: embed_execjson (subprocess exec-json, **CI hard gate**) vs
  embed_inprocess (EmbeddedSession, diagnostic-only — unfair vs TCP Postgres).
- Hard gate: point_lookup_with_index in embed_execjson; range_scan_name_prefix
  when index_impl is sorted_tree or btree (in-memory ordered map, not disk B-tree).
- ``index_impl`` autodetection: btree | sorted_tree | hash_map | unknown.
- Do not claim "as fast as Supabase" until CI publishes green gated rows +
  sorted_tree/btree indexed path (or an explicit hash_map footnote forever).

Env
---
  LIDB_ROOT / LIDB_EMBED  — lidb checkout or embed binary
  POSTGRES_URL            — optional; enables Postgres compare
  BENCH_ROWS / BENCH_WARMUP / BENCH_MEASURE
  HARDWARE_NOTE           — free-text runner description for the JSON payload
  OLTP_CONCURRENT_WORKERS / OLTP_CONCURRENT_OPS_PER_WORKER
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import statistics
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

# Scenario catalogs
SCENARIO_CORE = (
    "point_lookup_no_index",
    "point_lookup_with_index",
    "point_insert",
    "indexed_read_write_mix",
)
SCENARIO_ALL = SCENARIO_CORE + (
    "range_scan_name_prefix",
    "concurrent_readers",
)
SCENARIO_META = {
    "point_lookup_no_index": "diagnostic",
    "point_lookup_with_index": "gated",
    "point_insert": "soft",
    "indexed_read_write_mix": "soft",
    "range_scan_name_prefix": "diagnostic",
    "concurrent_readers": "soft",
}


def p95_ms(samples: list[float]) -> float:
    if not samples:
        return 0.0
    ordered = sorted(samples)
    return ordered[max(0, int(round(0.95 * (len(ordered) - 1))))]


def timing_stats(samples: list[float], *, wall_s: float | None = None, ops: int | None = None) -> dict:
    if not samples:
        out = {"mean_ms": 0.0, "p50_ms": 0.0, "p95_ms": 0.0, "n": 0}
    else:
        out = {
            "mean_ms": round(statistics.mean(samples), 4),
            "p50_ms": round(statistics.median(samples), 4),
            "p95_ms": round(p95_ms(samples), 4),
            "n": len(samples),
        }
    if wall_s is not None and ops is not None and wall_s > 0:
        out["ops_per_sec"] = round(ops / wall_s, 2)
        out["wall_s"] = round(wall_s, 4)
    return out


def time_fn(fn, *, warmup: int, measure: int) -> dict:
    for _ in range(warmup):
        fn()
    samples: list[float] = []
    t_wall0 = time.perf_counter()
    for _ in range(measure):
        t0 = time.perf_counter()
        fn()
        samples.append((time.perf_counter() - t0) * 1000.0)
    wall_s = time.perf_counter() - t_wall0
    return timing_stats(samples, wall_s=wall_s, ops=measure)


def find_lidb_root() -> Path:
    return Path(
        os.environ.get(
            "LIDB_ROOT",
            r"C:\Users\Julian\Documents\Programming\li\lidb",
        )
    )


def lidb_pin(root: Path) -> str:
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(root),
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            return proc.stdout.strip()
    except OSError:
        pass
    return "unknown"


def detect_index_impl(*, root: Path, data_dir: Path | None = None) -> str:
    """Detect lidb index_impl (btree|sorted_tree|hash_map|unknown) for honesty JSON.

    Prefer liorm.probe_index_impl when LIDB_ROOT is importable; else parse
    ``.lidb/migration_intent.txt`` or ``lidb_embed open`` stdout.
    """
    known = ("btree", "sorted_tree", "hash_map")
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    try:
        from liorm.embed_engine import probe_index_impl  # type: ignore

        got = probe_index_impl(data_dir)
        if got in known:
            return got
        if got and got != "unknown":
            return got
    except Exception:
        pass

    if data_dir is not None:
        intent = data_dir / ".lidb" / "migration_intent.txt"
        if intent.is_file():
            for line in intent.read_text(encoding="utf-8", errors="replace").splitlines():
                if line.startswith("index_impl="):
                    val = line.split("=", 1)[1].strip()
                    if val.startswith("hash_map"):
                        return "hash_map"
                    if val in known:
                        return val
                    if "sorted_tree" in val:
                        return "sorted_tree"
                    if "btree" in val:
                        return "btree"

    embed = find_embed()
    if embed is None:
        return "unknown"
    try:
        with tempfile.TemporaryDirectory(prefix="lb-oltp-idx-") as tmp:
            proc = subprocess.run(
                [str(embed), "open", tmp],
                capture_output=True,
                text=True,
                check=False,
            )
            for token in (proc.stdout or "").split():
                if token.startswith("index_impl="):
                    val = token.split("=", 1)[1].strip()
                    if val.startswith("hash_map"):
                        return "hash_map"
                    if val in known:
                        return val
            subprocess.run(
                [str(embed), "migrate", tmp],
                capture_output=True,
                text=True,
                check=False,
            )
            intent = Path(tmp) / ".lidb" / "migration_intent.txt"
            if intent.is_file():
                for line in intent.read_text(encoding="utf-8", errors="replace").splitlines():
                    if line.startswith("index_impl="):
                        val = line.split("=", 1)[1].strip()
                        if val.startswith("hash_map"):
                            return "hash_map"
                        if val in known:
                            return val
    except OSError:
        pass
    return "unknown"


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


def resolve_scenarios(spec: str) -> list[str]:
    key = spec.strip().lower()
    if key == "core":
        return list(SCENARIO_CORE)
    if key == "all":
        return list(SCENARIO_ALL)
    if key == "list":
        return []
    presets = {"core": SCENARIO_CORE, "all": SCENARIO_ALL}
    parts = [p.strip().lower() for p in spec.split(",") if p.strip()]
    out: list[str] = []
    for part in parts:
        if part in presets:
            out.extend(presets[part])
        elif part in SCENARIO_ALL:
            out.append(part)
        else:
            raise SystemExit(f"unknown scenarios: {[part]}; known={list(SCENARIO_ALL)} + presets core,all")
    # preserve order, dedupe
    seen: set[str] = set()
    ordered: list[str] = []
    for sid in out:
        if sid not in seen:
            seen.add(sid)
            ordered.append(sid)
    return ordered


def scenario_row(
    *,
    engine: str,
    scenario: str,
    index: bool | None,
    status: str,
    stats: dict | None = None,
    note: str | None = None,
    extra: dict | None = None,
) -> dict:
    row = {
        "engine": engine,
        "scenario": scenario,
        "gate_class": SCENARIO_META.get(scenario, "diagnostic"),
        "index": index,
        "status": status,
    }
    if stats:
        row.update(stats)
    else:
        row.update({"mean_ms": None, "p50_ms": None, "p95_ms": None, "n": 0})
    if note:
        row["note"] = note
    if extra:
        row.update(extra)
    return row


def run(
    *,
    rows: int,
    warmup: int,
    measure: int,
    mode: str,
    scenarios: list[str],
    concurrent_workers: int,
    concurrent_ops: int,
) -> dict:
    embed = find_embed()
    if embed is None:
        raise RuntimeError("lidb_embed not found — set LIDB_EMBED or LIDB_ROOT")

    root = find_lidb_root()
    pin = lidb_pin(root)
    want = set(scenarios)
    out_scenarios: list[dict] = []
    index_impl = "unknown"

    with tempfile.TemporaryDirectory(prefix="lb-oltp-") as tmp:
        data = Path(tmp) / "lidb"
        data.mkdir(parents=True, exist_ok=True)

        session = None
        lock = threading.Lock()
        concurrent_note = None

        if mode == "embed_inprocess":
            session = try_session(data)
            if session is None:
                raise RuntimeError(
                    "embed_inprocess requested but EmbeddedSession unavailable "
                    "(liorm/embed_engine + migrate). Use --mode embed_execjson or fix LIDB_ROOT."
                )
            concurrent_note = (
                "lidb concurrent_readers uses a mutex around EmbeddedSession "
                "(embed not assumed thread-safe) — soft/diagnostic throughput"
            )
        elif mode == "embed_execjson":
            subprocess.run(
                [str(embed), "migrate", str(data)],
                check=True,
                capture_output=True,
                text=True,
            )
            concurrent_note = (
                "lidb concurrent_readers uses parallel exec-json subprocesses "
                "(includes spawn cost)"
            )
        else:
            raise ValueError(f"unknown mode: {mode}")

        index_impl = detect_index_impl(root=root, data_dir=data)
        if index_impl in ("sorted_tree", "btree"):
            SCENARIO_META["range_scan_name_prefix"] = "gated"

        def exec_sql(sql: str, params: list[str] | None = None) -> list:
            if session is not None:
                with lock:
                    return session.exec_parameterized(sql, params or [])
            return embed_exec(embed, data, sql, params)

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

        no_idx = None
        if "point_lookup_no_index" in want:
            no_idx = time_fn(lidb_lookup, warmup=warmup, measure=measure)
            out_scenarios.append(
                scenario_row(
                    engine="lidb",
                    scenario="point_lookup_no_index",
                    index=False,
                    status="measured",
                    stats=no_idx,
                )
            )

        indexed_ok = True
        try:
            exec_sql(
                "CREATE INDEX IF NOT EXISTS idx_bench_items_name ON bench_items (name)"
            )
        except Exception:
            indexed_ok = False

        with_idx = None
        if "point_lookup_with_index" in want:
            if indexed_ok:
                with_idx = time_fn(lidb_lookup, warmup=warmup, measure=measure)
                extra = {}
                if no_idx and no_idx["p95_ms"] > 0:
                    extra["speedup_vs_no_index_p95"] = round(
                        no_idx["p95_ms"] / with_idx["p95_ms"], 4
                    )
                out_scenarios.append(
                    scenario_row(
                        engine="lidb",
                        scenario="point_lookup_with_index",
                        index=True,
                        status="measured",
                        stats=with_idx,
                        extra=extra,
                    )
                )
            else:
                out_scenarios.append(
                    scenario_row(
                        engine="lidb",
                        scenario="point_lookup_with_index",
                        index=True,
                        status="index_unsupported",
                        note="CREATE INDEX not available in this lidb_embed build",
                    )
                )

        if "point_insert" in want:
            def lidb_insert() -> None:
                exec_sql(
                    "INSERT INTO bench_items (id, name, owner_id) VALUES (?, ?, ?)",
                    [str(uuid.uuid4()), f"ins-{uuid.uuid4().hex[:8]}", str(uuid.uuid4())],
                )

            ins = time_fn(lidb_insert, warmup=warmup, measure=measure)
            out_scenarios.append(
                scenario_row(
                    engine="lidb",
                    scenario="point_insert",
                    index=None,
                    status="measured",
                    stats=ins,
                )
            )

        if "indexed_read_write_mix" in want:
            if not indexed_ok:
                out_scenarios.append(
                    scenario_row(
                        engine="lidb",
                        scenario="indexed_read_write_mix",
                        index=True,
                        status="index_unsupported",
                        note="CREATE INDEX required for mix scenario",
                    )
                )
            else:
                counter = {"i": 0}

                def lidb_mix() -> None:
                    counter["i"] += 1
                    if counter["i"] % 5 == 0:
                        exec_sql(
                            "INSERT INTO bench_items (id, name, owner_id) VALUES (?, ?, ?)",
                            [
                                str(uuid.uuid4()),
                                f"mix-{uuid.uuid4().hex[:8]}",
                                str(uuid.uuid4()),
                            ],
                        )
                    else:
                        lidb_lookup()

                mix = time_fn(lidb_mix, warmup=warmup, measure=measure)
                out_scenarios.append(
                    scenario_row(
                        engine="lidb",
                        scenario="indexed_read_write_mix",
                        index=True,
                        status="measured",
                        stats=mix,
                        note="80% indexed SELECT / 20% INSERT",
                    )
                )

        if "range_scan_name_prefix" in want:
            def lidb_range() -> None:
                out = exec_sql(
                    "SELECT id, name FROM bench_items WHERE name LIKE ? LIMIT 50",
                    ["lookup-%"],
                )
                if not out:
                    raise RuntimeError("lidb range miss")

            rng = time_fn(lidb_range, warmup=warmup, measure=measure)
            out_scenarios.append(
                scenario_row(
                    engine="lidb",
                    scenario="range_scan_name_prefix",
                    index=indexed_ok,
                    status="measured",
                    stats=rng,
                    note="sorted_tree in-memory ordered map (not disk B-tree); gated when index_impl sorted_tree/btree",
                )
            )

        if "concurrent_readers" in want:
            if not indexed_ok:
                out_scenarios.append(
                    scenario_row(
                        engine="lidb",
                        scenario="concurrent_readers",
                        index=True,
                        status="index_unsupported",
                        note="CREATE INDEX required",
                    )
                )
            else:
                total_ops = concurrent_workers * concurrent_ops

                def worker_ops(_: int) -> list[float]:
                    samples: list[float] = []
                    for _j in range(concurrent_ops):
                        t0 = time.perf_counter()
                        lidb_lookup()
                        samples.append((time.perf_counter() - t0) * 1000.0)
                    return samples

                t0 = time.perf_counter()
                all_samples: list[float] = []
                with ThreadPoolExecutor(max_workers=concurrent_workers) as pool:
                    futs = [pool.submit(worker_ops, w) for w in range(concurrent_workers)]
                    for fut in as_completed(futs):
                        all_samples.extend(fut.result())
                wall_s = time.perf_counter() - t0
                stats = timing_stats(all_samples, wall_s=wall_s, ops=total_ops)
                out_scenarios.append(
                    scenario_row(
                        engine="lidb",
                        scenario="concurrent_readers",
                        index=True,
                        status="measured",
                        stats=stats,
                        note=concurrent_note,
                        extra={
                            "workers": concurrent_workers,
                            "ops_per_worker": concurrent_ops,
                        },
                    )
                )

        if session is not None:
            session.close()

        pg = pg_connect()
        if pg:
            try:
                pg_target = pg_prepare(pg, rows)
                cur = pg.cursor()
                pg_url = os.environ.get("POSTGRES_URL") or os.environ.get("DATABASE_URL")

                def pg_lookup() -> None:
                    cur.execute(
                        "SELECT id, name FROM bench_items WHERE name = %s",
                        (pg_target,),
                    )
                    if not cur.fetchone():
                        raise RuntimeError("postgres lookup miss")

                pg_no = None
                if "point_lookup_no_index" in want:
                    pg_no = time_fn(pg_lookup, warmup=warmup, measure=measure)
                    out_scenarios.append(
                        scenario_row(
                            engine="postgres",
                            scenario="point_lookup_no_index",
                            index=False,
                            status="measured",
                            stats=pg_no,
                        )
                    )

                cur.execute("CREATE INDEX idx_bench_items_name ON bench_items (name)")
                pg.commit()
                cur.execute("ANALYZE bench_items")
                pg.commit()

                if "point_lookup_with_index" in want:
                    pg_yes = time_fn(pg_lookup, warmup=warmup, measure=measure)
                    extra = {}
                    if pg_no and pg_no["p95_ms"] > 0:
                        extra["speedup_vs_no_index_p95"] = round(
                            pg_no["p95_ms"] / pg_yes["p95_ms"], 4
                        )
                    out_scenarios.append(
                        scenario_row(
                            engine="postgres",
                            scenario="point_lookup_with_index",
                            index=True,
                            status="measured",
                            stats=pg_yes,
                            extra=extra,
                        )
                    )

                if "point_insert" in want:
                    def pg_insert() -> None:
                        cur.execute(
                            "INSERT INTO bench_items (id, name, owner_id) VALUES (%s, %s, %s)",
                            (
                                str(uuid.uuid4()),
                                f"ins-{uuid.uuid4().hex[:8]}",
                                str(uuid.uuid4()),
                            ),
                        )
                        pg.commit()

                    pg_ins = time_fn(pg_insert, warmup=warmup, measure=measure)
                    out_scenarios.append(
                        scenario_row(
                            engine="postgres",
                            scenario="point_insert",
                            index=None,
                            status="measured",
                            stats=pg_ins,
                        )
                    )

                if "indexed_read_write_mix" in want:
                    counter = {"i": 0}

                    def pg_mix() -> None:
                        counter["i"] += 1
                        if counter["i"] % 5 == 0:
                            cur.execute(
                                "INSERT INTO bench_items (id, name, owner_id) VALUES (%s, %s, %s)",
                                (
                                    str(uuid.uuid4()),
                                    f"mix-{uuid.uuid4().hex[:8]}",
                                    str(uuid.uuid4()),
                                ),
                            )
                            pg.commit()
                        else:
                            pg_lookup()

                    pg_mix_stats = time_fn(pg_mix, warmup=warmup, measure=measure)
                    out_scenarios.append(
                        scenario_row(
                            engine="postgres",
                            scenario="indexed_read_write_mix",
                            index=True,
                            status="measured",
                            stats=pg_mix_stats,
                            note="80% indexed SELECT / 20% INSERT",
                        )
                    )

                if "range_scan_name_prefix" in want:
                    def pg_range() -> None:
                        cur.execute(
                            "SELECT id, name FROM bench_items WHERE name LIKE %s LIMIT 50",
                            ("lookup-%",),
                        )
                        if not cur.fetchall():
                            raise RuntimeError("postgres range miss")

                    pg_rng = time_fn(pg_range, warmup=warmup, measure=measure)
                    out_scenarios.append(
                        scenario_row(
                            engine="postgres",
                            scenario="range_scan_name_prefix",
                            index=True,
                            status="measured",
                            stats=pg_rng,
                        )
                    )

                if "concurrent_readers" in want:
                    total_ops = concurrent_workers * concurrent_ops

                    def pg_worker(_: int) -> list[float]:
                        conn = psycopg2_connect(pg_url)
                        try:
                            c = conn.cursor()
                            samples: list[float] = []
                            for _j in range(concurrent_ops):
                                t0 = time.perf_counter()
                                c.execute(
                                    "SELECT id, name FROM bench_items WHERE name = %s",
                                    (pg_target,),
                                )
                                if not c.fetchone():
                                    raise RuntimeError("postgres concurrent miss")
                                samples.append((time.perf_counter() - t0) * 1000.0)
                            c.close()
                            return samples
                        finally:
                            conn.close()

                    t0 = time.perf_counter()
                    all_samples: list[float] = []
                    with ThreadPoolExecutor(max_workers=concurrent_workers) as pool:
                        futs = [
                            pool.submit(pg_worker, w) for w in range(concurrent_workers)
                        ]
                        for fut in as_completed(futs):
                            all_samples.extend(fut.result())
                    wall_s = time.perf_counter() - t0
                    stats = timing_stats(all_samples, wall_s=wall_s, ops=total_ops)
                    out_scenarios.append(
                        scenario_row(
                            engine="postgres",
                            scenario="concurrent_readers",
                            index=True,
                            status="measured",
                            stats=stats,
                            note="one Postgres connection per worker",
                            extra={
                                "workers": concurrent_workers,
                                "ops_per_worker": concurrent_ops,
                            },
                        )
                    )

                cur.close()
            finally:
                pg.close()

    # Attach ratios (P95 and ops/sec where both present)
    by_key = {
        (s["engine"], s["scenario"]): s
        for s in out_scenarios
        if s["status"] == "measured"
    }
    for s in out_scenarios:
        if s["engine"] != "lidb" or s["status"] != "measured":
            continue
        pg_row = by_key.get(("postgres", s["scenario"]))
        if not pg_row:
            continue
        if pg_row.get("p95_ms"):
            s["ratio_vs_postgres_p95"] = round(s["p95_ms"] / pg_row["p95_ms"], 4)
        if pg_row.get("ops_per_sec") and s.get("ops_per_sec"):
            # higher ops is better → postgres/lidb so <1 means lidb faster
            s["ratio_vs_postgres_ops"] = round(
                pg_row["ops_per_sec"] / s["ops_per_sec"], 4
            )

    hardware_note = os.environ.get("HARDWARE_NOTE", "").strip() or (
        "unspecified — set HARDWARE_NOTE for reproducible same-hardware claims"
    )

    return {
        "suite": "librebase-oltp-index-compare",
        "rows_seeded": rows,
        "warmup": warmup,
        "measure": measure,
        "mode": mode,
        "lidb_mode": mode,  # back-compat alias
        "scenarios_selected": scenarios,
        "embed": str(embed),
        "lidb_pin": pin,
        "lidb_root": str(root),
        "runner_os": platform.platform(),
        "hardware_note": hardware_note,
        "index_impl": index_impl,
        "postgres": bool(
            os.environ.get("POSTGRES_URL") or os.environ.get("DATABASE_URL")
        ),
        "honesty": (
            f"Aims only until CI green. mode={mode} — "
            + (
                "embed_execjson is the CI hard-gate path (subprocess exec-json vs TCP Postgres)."
                if mode == "embed_execjson"
                else "embed_inprocess is diagnostic-only (unfair vs TCP Postgres)."
            )
            + f" index_impl={index_impl} — "
            + (
                "sorted_tree is in-memory ordered map (not disk B-tree / Postgres parity); "
                "range_scan is gated when index_impl is sorted_tree/btree."
                if index_impl == "sorted_tree"
                else "btree claim reserved for page B-tree; "
                if index_impl == "btree"
                else "hash_map — not B-tree / Postgres parity; "
            )
                + " gated marketing claim needs multi-day CI PASS + PH-DB-7 (or forever footnote)."
        ),
        "scenarios": out_scenarios,
    }


def psycopg2_connect(url: str | None):
    import psycopg2  # type: ignore

    if not url:
        raise RuntimeError("POSTGRES_URL required for concurrent Postgres workers")
    return psycopg2.connect(url)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rows", type=int, default=int(os.environ.get("BENCH_ROWS", "5000")))
    ap.add_argument("--warmup", type=int, default=int(os.environ.get("BENCH_WARMUP", "20")))
    ap.add_argument(
        "--measure", type=int, default=int(os.environ.get("BENCH_MEASURE", "100"))
    )
    ap.add_argument(
        "--mode",
        choices=("embed_inprocess", "embed_execjson"),
        default=os.environ.get("OLTP_MODE", "embed_execjson"),
        help="Fairness mode (default: embed_execjson — CI hard gate)",
    )
    ap.add_argument(
        "--scenarios",
        default=os.environ.get("OLTP_SCENARIOS", "core"),
        help="all | core | list | comma-separated scenario ids",
    )
    ap.add_argument(
        "--concurrent-workers",
        type=int,
        default=int(os.environ.get("OLTP_CONCURRENT_WORKERS", "4")),
    )
    ap.add_argument(
        "--concurrent-ops",
        type=int,
        default=int(os.environ.get("OLTP_CONCURRENT_OPS_PER_WORKER", "50")),
    )
    ap.add_argument(
        "--json-out",
        type=Path,
        default=REPO / "benchmarks" / "oltp-compare" / "results" / "latest.json",
    )
    args = ap.parse_args()

    if args.scenarios.strip().lower() == "list":
        print("Scenarios:")
        for sid in SCENARIO_ALL:
            print(f"  {sid:28} gate_class={SCENARIO_META[sid]}")
        print("Presets: core =", ", ".join(SCENARIO_CORE))
        print("         all  =", ", ".join(SCENARIO_ALL))
        return 0

    try:
        selected = resolve_scenarios(args.scenarios)
        payload = run(
            rows=args.rows,
            warmup=args.warmup,
            measure=args.measure,
            mode=args.mode,
            scenarios=selected,
            concurrent_workers=args.concurrent_workers,
            concurrent_ops=args.concurrent_ops,
        )
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(
        f"wrote {args.json_out} mode={payload['mode']} pin={payload['lidb_pin']} "
        f"index_impl={payload['index_impl']}"
    )
    for s in payload["scenarios"]:
        print(
            f"  {s['engine']:8} {s['scenario']:28} "
            f"p95={s.get('p95_ms')} ops={s.get('ops_per_sec')} "
            f"status={s['status']} gate={s.get('gate_class')} "
            f"vs_pg={s.get('ratio_vs_postgres_p95')}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
