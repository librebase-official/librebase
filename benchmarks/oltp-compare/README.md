# Librebase OLTP compare (with / without indexes)

Honest latency / throughput compare of **lidb embed** vs **Postgres** on shared schemas.

## Modes (fairness)

| Mode | lidb | Postgres | Use |
|------|------|----------|-----|
| `embed_inprocess` (default) | `EmbeddedSession` in-process | TCP | Engine microbench — **gated** path today |
| `embed_execjson` | `lidb_embed exec-json` subprocess | TCP | Includes spawn cost (diagnostic) |

JSON always records `mode`, `lidb_pin` (`git rev-parse` of `LIDB_ROOT`), `runner_os`, `hardware_note`, and `index_impl: hash_map`.

In-process lidb vs TCP Postgres is **not** a fair process-boundary compare. Treat gated green rows as evidence artifacts with that label until a `fair_sql` mode exists.

## Scenarios

| Scenario | Work | Gate class |
|----------|------|------------|
| `point_lookup_no_index` | `SELECT … WHERE name = ?` after seeding N rows | diagnostic |
| `point_lookup_with_index` | Same after `CREATE INDEX … (name)` | **gated** — `ratio_vs_postgres_p95 ≤ 1.2` |
| `point_insert` | single-row `INSERT` | **soft** — ≤ **1.5** first release (warn; hard if `OLTP_SOFT_FAIL=1`) |
| `indexed_read_write_mix` | 80% indexed SELECT / 20% INSERT | soft (ops/sec + P95) |
| `range_scan_name_prefix` | `WHERE name LIKE 'lookup-%' LIMIT 50` | diagnostic until btree (P5) |
| `concurrent_readers` | N threads × M lookups | soft; report `ops_per_sec` |

Presets: `--scenarios core` (CI) = lookups + insert + mix; `--scenarios all` adds range + concurrent; `--scenarios list` prints ids.

## Gated vs diagnostic

| Class | Meaning |
|-------|---------|
| **gated** | `check_gate.py` hard-fails CI when breached (`point_lookup_with_index`) |
| **soft** | Documented threshold; warn by default (`OLTP_SOFT_RATIO_MAX=1.5` for insert/mix) |
| **diagnostic** | Recorded only — no pass/fail |

Marketing “on par / Supabase-class” still requires P1 CI green **and** P5 btree (or an explicit forever `hash_map` footnote). PH-DB-7 lean RSS is a separate lidb gate.

## Honesty

- **Aims until CI green** — do not market “as fast as Supabase” from a laptop run alone.
- lidb indexed path needs embed with **CREATE INDEX**. Older embeds → `index_unsupported` (gate **fails**).
- `index_impl: hash_map` — **not** Postgres B-tree parity.
- `ratio_vs_postgres_p95` = lidb_p95 / postgres_p95 (lower = faster than Postgres on that run).
- Concurrent lidb `embed_inprocess` uses a mutex around the session (not true parallel engine concurrency).

## Run

```powershell
$env:LIDB_ROOT = "C:\Users\Julian\Documents\Programming\li\lidb"
$env:LIDB_EMBED = "$env:LIDB_ROOT\build\smoke\Release\lidb_embed.exe"
$env:POSTGRES_URL = "postgresql://postgres:postgres@127.0.0.1:5433/postgres"
$env:HARDWARE_NOTE = "local win32 + lb-pg-bench:5433"
python benchmarks/oltp-compare/run_compare.py --mode embed_inprocess --scenarios core --rows 10000 --warmup 30 --measure 200
python benchmarks/oltp-compare/check_gate.py
```

Env knobs: `OLTP_RATIO_MAX` (default `1.2`), `OLTP_SOFT_RATIO_MAX` (default `1.5`), `OLTP_SOFT_FAIL`, `OLTP_MODE`, `OLTP_SCENARIOS`.

## CI

Workflow: [`.github/workflows/oltp-compare.yml`](../../.github/workflows/oltp-compare.yml) (`workflow_dispatch` / nightly).

1. Parse lidb SHA from [`docs/li-dependency-pins.md`](../../docs/li-dependency-pins.md).
2. Checkout `li-langverse/lidb` at that pin (`LIDB_CHECKOUT_TOKEN` when the mirror is private).
3. Build smoke `lidb_embed` (`cmake` → `build/smoke`).
4. Run `--scenarios core` + `check_gate.py` — **fail** on skip, `index_unsupported`, or gated ratio breach.
5. Upload `latest.json` with `if: always()`.

Debug-only: `workflow_dispatch` input `force_skip_ok` allows exit 0 on missing embed (not for schedule).

## Latest local sample (aims only)

Historical laptop sample (pre-gate harness) lives in [`results/latest.json`](results/latest.json). Re-run locally and prefer CI artifacts for claims.
