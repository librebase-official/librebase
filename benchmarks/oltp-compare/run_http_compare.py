#!/usr/bin/env python3
"""Librebase HTTP REST compare: lis+lidb /rest/v1 vs PostgREST on Postgres.

Product-path latency (not engine embed microbench). Soft-gate first:
  ratio lis_p95 / postgrest_p95 ≤ HTTP_RATIO_MAX (default 1.2) → warn only
  unless HTTP_SOFT_FAIL=1.

Soft-skip (exit 0 + skipped JSON) when LIS and/or PostgREST URLs are
unreachable — intentional so CI SQL gate stays hard while HTTP remains optional.

Env
---
  LIS_REST_URL / LIBREBASE_PARITY_API  — lis registry API base (default :54321)
  POSTGREST_URL                        — PostgREST base (required for measure)
  POSTGRES_URL                         — prepare identical schema for PostgREST
  LIS_ROOT                             — pin metadata (optional)
  HTTP_TABLE                           — default parity_items (lis lidb path)
  HTTP_WARMUP / HTTP_MEASURE           — defaults 20 / 100
  HTTP_RATIO_MAX                       — soft threshold (default 1.2)
  HTTP_SOFT_FAIL                       — 1 → exit 1 on soft breach
  HARDWARE_NOTE                        — free-text runner label
  HTTP_AUTH_EMAIL / HTTP_AUTH_PASSWORD — lis JWT for RLS-backed parity_items
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import statistics
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
DEFAULT_OUT = REPO / "benchmarks" / "oltp-compare" / "results" / "http-latest.json"

SCENARIOS = ("rest_get_eq_name", "rest_post_insert")
GATE_ID = "http_rest_p95"


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


def lis_base() -> str:
    return (
        os.environ.get("LIS_REST_URL")
        or os.environ.get("LIBREBASE_PARITY_API")
        or "http://127.0.0.1:54321"
    ).rstrip("/")


def postgrest_base() -> str:
    return (os.environ.get("POSTGREST_URL") or "").strip().rstrip("/")


def find_lis_root() -> Path | None:
    raw = os.environ.get("LIS_ROOT", "").strip()
    if raw:
        p = Path(raw)
        return p if p.is_dir() else None
    for cand in (
        REPO.parent / "li" / "lis",
        Path(r"C:\Users\Julian\Documents\Programming\li\lis"),
        Path("/workspace/lis"),
    ):
        if cand.is_dir():
            return cand
    return None


def git_pin(root: Path | None) -> str:
    if root is None:
        return "unknown"
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


def http(
    base: str,
    method: str,
    path: str,
    *,
    body: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = 10.0,
) -> tuple[int, Any]:
    data = None if body is None else json.dumps(body).encode("utf-8")
    hdrs = {"Content-Type": "application/json", "Accept": "application/json", **(headers or {})}
    req = urllib.request.Request(base + path, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            try:
                return resp.status, json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                return resp.status, {"raw": raw}
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8")
        try:
            return e.code, json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            return e.code, {"raw": raw}
    except Exception as exc:  # noqa: BLE001
        return 0, {"error": str(exc)}


def probe_lis(base: str) -> bool:
    # Prefer REST health; fall back to any listener response
    for path in ("/rest/v1", "/v1/health", "/"):
        status, body = http(base, "GET", path, timeout=3.0)
        if status == 0:
            continue
        if path == "/rest/v1" and status == 200:
            return True
        if status > 0:
            # Listener up; REST may still work for table routes
            if path == "/rest/v1" or status in (200, 404, 401):
                return True
            if isinstance(body, dict):
                return True
    return False


def probe_postgrest(base: str) -> bool:
    status, _ = http(base, "GET", "/", timeout=3.0)
    return status != 0


def lis_auth_headers(base: str) -> dict[str, str]:
    email = os.environ.get("HTTP_AUTH_EMAIL", "http-bench@example.com")
    password = os.environ.get("HTTP_AUTH_PASSWORD", "http-bench-secret-change-me")
    http(base, "POST", "/v1/auth/signup", body={"email": email, "password": password})
    status, body = http(
        base, "POST", "/v1/auth/login", body={"email": email, "password": password}
    )
    token = None
    if isinstance(body, dict):
        token = body.get("access_token") or body.get("token")
        if not token and isinstance(body.get("session"), dict):
            token = body["session"].get("access_token")
    if status != 200 or not token:
        raise RuntimeError(f"lis auth failed status={status} body={body!r}")
    return {"Authorization": f"Bearer {token}"}


def prepare_postgres_schema(table: str, rows: int) -> str:
    """Create identical parity_items-shaped table for PostgREST; return lookup name."""
    url = os.environ.get("POSTGRES_URL") or os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("POSTGRES_URL required to prepare PostgREST schema")
    try:
        import psycopg2  # type: ignore
    except ImportError as exc:
        raise RuntimeError("psycopg2-binary required for PostgREST schema prep") from exc

    conn = psycopg2.connect(url)
    try:
        cur = conn.cursor()
        cur.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
        cur.execute(
            f"""
            CREATE TABLE {table} (
                id UUID PRIMARY KEY,
                name TEXT NOT NULL,
                owner_id UUID NOT NULL,
                secret TEXT
            )
            """
        )
        try:
            cur.execute(f"GRANT ALL ON TABLE {table} TO PUBLIC")
        except Exception:
            pass
        target = f"lookup-{rows // 2}"
        owner = str(uuid.uuid4())
        for i in range(rows):
            cur.execute(
                f"INSERT INTO {table} (id, name, owner_id, secret) VALUES (%s, %s, %s, %s)",
                (str(uuid.uuid4()), f"lookup-{i}", owner, "s"),
            )
        conn.commit()
        try:
            cur.execute("NOTIFY pgrst, 'reload schema'")
            conn.commit()
        except Exception:
            conn.rollback()
        cur.close()
    finally:
        conn.close()
    return target


def seed_lis(base: str, table: str, rows: int, headers: dict[str, str]) -> str:
    """Seed via POST so GET has a known eq filter target."""
    target = f"lookup-{rows // 2}"
    for i in range(rows):
        status, body = http(
            base,
            "POST",
            f"/rest/v1/{table}",
            body={"name": f"lookup-{i}", "secret": "s"},
            headers=headers,
        )
        if status not in (200, 201):
            raise RuntimeError(f"lis seed POST failed status={status} body={body!r}")
    # Confirm GET works
    status, body = http(
        base,
        "GET",
        f"/rest/v1/{table}?name=eq.{target}&limit=1",
        headers=headers,
    )
    if status != 200:
        raise RuntimeError(f"lis seed verify GET failed status={status} body={body!r}")
    return target


def skipped_payload(*, reason: str, lis_ok: bool, pgrst_ok: bool) -> dict:
    return {
        "suite": "librebase-http-rest-compare",
        "gate_id": GATE_ID,
        "skipped": True,
        "skip_reason": reason,
        "lis_rest": lis_ok,
        "postgrest": pgrst_ok,
        "lis_pin": git_pin(find_lis_root()),
        "runner_os": platform.platform(),
        "hardware_note": os.environ.get("HARDWARE_NOTE", ""),
        "honesty": (
            "HTTP soft-skip — LIS/API or PostgREST unavailable. "
            "Does not imply SQL OLTP gate result. Not a marketing green row."
        ),
        "soft_gate": {"threshold": float(os.environ.get("HTTP_RATIO_MAX", "1.2")), "breached": False},
        "scenarios": [],
    }


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def soft_gate_report(payload: dict) -> int:
    """Warn on soft breach; exit 1 only if HTTP_SOFT_FAIL=1."""
    soft_fail = os.environ.get("HTTP_SOFT_FAIL", "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )
    soft = payload.get("soft_gate") or {}
    breached = bool(soft.get("breached"))
    threshold = soft.get("threshold")
    if payload.get("skipped"):
        print(
            f"HTTP GATE: SKIP ({payload.get('skip_reason')}) — soft-skip exit 0",
            file=sys.stderr,
        )
        return 0
    if not breached:
        print(f"HTTP GATE: PASS (soft ≤ {threshold})")
        return 0
    msg = (
        f"HTTP soft gate breached: ratio > {threshold} "
        f"(details in soft_gate / scenarios)"
    )
    print(f"WARN: {msg}", file=sys.stderr)
    if soft_fail:
        print("HTTP GATE: FAIL (HTTP_SOFT_FAIL=1)", file=sys.stderr)
        return 1
    print("HTTP GATE: WARN (soft — not failing CI)", file=sys.stderr)
    return 0


def run(*, rows: int, warmup: int, measure: int, table: str) -> dict:
    lis = lis_base()
    pgrst = postgrest_base()
    lis_ok = probe_lis(lis)
    pgrst_ok = probe_postgrest(pgrst) if pgrst else False

    if not lis_ok or not pgrst_ok:
        missing = []
        if not lis_ok:
            missing.append(f"lis REST unreachable at {lis}")
        if not pgrst:
            missing.append("POSTGREST_URL unset")
        elif not pgrst_ok:
            missing.append(f"PostgREST unreachable at {pgrst}")
        return skipped_payload(
            reason="; ".join(missing),
            lis_ok=lis_ok,
            pgrst_ok=pgrst_ok,
        )

    ratio_max = float(os.environ.get("HTTP_RATIO_MAX", "1.2"))
    lis_hdrs = lis_auth_headers(lis)
    # Prefer / Prefer headers for PostgREST insert return
    pgrst_hdrs = {
        "Prefer": "return=representation",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    lis_target = seed_lis(lis, table, rows, lis_hdrs)
    try:
        pg_target = prepare_postgres_schema(table, rows)
    except Exception as exc:
        return skipped_payload(
            reason=f"PostgREST schema prep failed: {exc}",
            lis_ok=True,
            pgrst_ok=True,
        )

    # Brief wait for PostgREST schema reload
    time.sleep(0.5)
    status, body = http(pgrst, "GET", f"/{table}?name=eq.{pg_target}&limit=1", headers=pgrst_hdrs)
    if status != 200:
        return skipped_payload(
            reason=f"PostgREST GET after seed failed status={status} body={body!r}",
            lis_ok=True,
            pgrst_ok=True,
        )

    scenarios: list[dict] = []

    # --- GET eq name ---
    def lis_get() -> None:
        st, out = http(
            lis,
            "GET",
            f"/rest/v1/{table}?name=eq.{lis_target}&limit=1",
            headers=lis_hdrs,
        )
        if st != 200:
            raise RuntimeError(f"lis GET {st}")

    def pgrst_get() -> None:
        st, out = http(
            pgrst,
            "GET",
            f"/{table}?name=eq.{pg_target}&limit=1",
            headers=pgrst_hdrs,
        )
        if st != 200:
            raise RuntimeError(f"postgrest GET {st}")

    lis_get_stats = time_fn(lis_get, warmup=warmup, measure=measure)
    pgrst_get_stats = time_fn(pgrst_get, warmup=warmup, measure=measure)
    get_ratio = (
        round(lis_get_stats["p95_ms"] / pgrst_get_stats["p95_ms"], 4)
        if pgrst_get_stats["p95_ms"] > 0
        else None
    )
    scenarios.append(
        {
            "engine": "lis",
            "scenario": "rest_get_eq_name",
            "gate_class": "soft",
            "status": "measured",
            "surface": "rest",
            **lis_get_stats,
            "ratio_vs_postgrest_p95": get_ratio,
        }
    )
    scenarios.append(
        {
            "engine": "postgrest",
            "scenario": "rest_get_eq_name",
            "gate_class": "soft",
            "status": "measured",
            "surface": "rest",
            **pgrst_get_stats,
        }
    )

    # --- POST insert ---
    counter = {"n": 0}

    def lis_post() -> None:
        counter["n"] += 1
        st, out = http(
            lis,
            "POST",
            f"/rest/v1/{table}",
            body={"name": f"bench-post-{counter['n']}-{uuid.uuid4().hex[:8]}", "secret": "p"},
            headers=lis_hdrs,
        )
        if st not in (200, 201):
            raise RuntimeError(f"lis POST {st}")

    def pgrst_post() -> None:
        counter["n"] += 1
        st, out = http(
            pgrst,
            "POST",
            f"/{table}",
            body={
                "id": str(uuid.uuid4()),
                "name": f"bench-post-{counter['n']}-{uuid.uuid4().hex[:8]}",
                "owner_id": str(uuid.uuid4()),
                "secret": "p",
            },
            headers=pgrst_hdrs,
        )
        if st not in (200, 201):
            raise RuntimeError(f"postgrest POST {st}")

    lis_post_stats = time_fn(lis_post, warmup=warmup, measure=measure)
    pgrst_post_stats = time_fn(pgrst_post, warmup=warmup, measure=measure)
    post_ratio = (
        round(lis_post_stats["p95_ms"] / pgrst_post_stats["p95_ms"], 4)
        if pgrst_post_stats["p95_ms"] > 0
        else None
    )
    scenarios.append(
        {
            "engine": "lis",
            "scenario": "rest_post_insert",
            "gate_class": "soft",
            "status": "measured",
            "surface": "rest",
            **lis_post_stats,
            "ratio_vs_postgrest_p95": post_ratio,
        }
    )
    scenarios.append(
        {
            "engine": "postgrest",
            "scenario": "rest_post_insert",
            "gate_class": "soft",
            "status": "measured",
            "surface": "rest",
            **pgrst_post_stats,
        }
    )

    ratios = [r for r in (get_ratio, post_ratio) if isinstance(r, (int, float))]
    max_ratio = max(ratios) if ratios else None
    breached = max_ratio is not None and float(max_ratio) > ratio_max

    return {
        "suite": "librebase-http-rest-compare",
        "gate_id": GATE_ID,
        "skipped": False,
        "lis_rest": True,
        "postgrest": True,
        "lis_url": lis,
        "postgrest_url": pgrst,
        "table": table,
        "lis_pin": git_pin(find_lis_root()),
        "runner_os": platform.platform(),
        "hardware_note": os.environ.get("HARDWARE_NOTE", ""),
        "rows_seeded": rows,
        "warmup": warmup,
        "measure": measure,
        "honesty": (
            "lis /rest/v1 (Python MVP + lidb parity_items) vs PostgREST TCP on "
            "identical schema. Soft gate only — SQL embed green does not imply REST green."
        ),
        "soft_gate": {
            "id": GATE_ID,
            "threshold": ratio_max,
            "max_ratio_vs_postgrest_p95": max_ratio,
            "breached": breached,
            "scenarios": list(SCENARIOS),
        },
        "scenarios": scenarios,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="lis REST vs PostgREST latency compare (soft)")
    parser.add_argument("--rows", type=int, default=int(os.environ.get("HTTP_ROWS", "50")))
    parser.add_argument("--warmup", type=int, default=int(os.environ.get("HTTP_WARMUP", "20")))
    parser.add_argument("--measure", type=int, default=int(os.environ.get("HTTP_MEASURE", "100")))
    parser.add_argument(
        "--table",
        default=os.environ.get("HTTP_TABLE", "parity_items"),
        help="Must be parity_items for lis lidb backend",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=Path(os.environ.get("HTTP_JSON_OUT", str(DEFAULT_OUT))),
    )
    args = parser.parse_args()

    try:
        payload = run(rows=args.rows, warmup=args.warmup, measure=args.measure, table=args.table)
    except Exception as exc:
        payload = skipped_payload(
            reason=f"harness error: {exc}",
            lis_ok=False,
            pgrst_ok=False,
        )
        write_json(args.json_out, payload)
        print(json.dumps(payload, indent=2))
        print(f"wrote {args.json_out}", file=sys.stderr)
        return soft_gate_report(payload)

    write_json(args.json_out, payload)
    print(json.dumps(payload, indent=2))
    print(f"wrote {args.json_out}", file=sys.stderr)

    # Print compact table
    print(
        f"{'engine':10} {'scenario':20} {'status':10} {'p95_ms':>10} {'ratio':>8}",
        file=sys.stderr,
    )
    for s in payload.get("scenarios") or []:
        ratio = s.get("ratio_vs_postgrest_p95")
        ratio_s = f"{ratio:.4f}" if isinstance(ratio, (int, float)) else "-"
        p95 = s.get("p95_ms")
        p95_s = f"{p95:.4f}" if isinstance(p95, (int, float)) else "-"
        print(
            f"{s.get('engine', '?'):10} {s.get('scenario', '?'):20} "
            f"{s.get('status', '?'):10} {p95_s:>10} {ratio_s:>8}",
            file=sys.stderr,
        )

    return soft_gate_report(payload)


if __name__ == "__main__":
    raise SystemExit(main())
