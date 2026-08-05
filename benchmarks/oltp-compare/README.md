# Librebase OLTP compare (with / without indexes)

Honest latency compare of **lidb embed** vs **Postgres** on point lookups.

## What it measures

| Scenario | Meaning |
|----------|---------|
| `point_lookup_no_index` | `SELECT … WHERE name = ?` after seeding N rows, no secondary index |
| `point_lookup_with_index` | Same lookup after `CREATE INDEX … ON bench_items (name)` |

For each measured pair, reports mean / P50 / P95 (ms) and `ratio_vs_postgres_p95` when `POSTGRES_URL` is set.

## Honesty

- **Aims until CI green** — do not market “as fast as Supabase” from a laptop run alone.
- lidb indexed path needs embed with **CREATE INDEX** (`feat/wave-b-create-index`+). Older embeds report `index_unsupported`.
- lidb index is an in-memory equality map when present — **not** Postgres B-tree parity.
- SQL-file migrate may still skip indexes until allowlisted CREATE INDEX apply lands.
- `ratio_vs_postgres_p95` is lidb_p95 / postgres_p95 (lower = faster than Postgres on that run). Local ratios can favor in-process embed vs TCP Postgres; treat as evidence artifact, not a product claim.

## Latest local sample (aims only)

`feat/wave-b-create-index` @ `e9f8570`, in-process EmbeddedSession vs **Postgres 16** (`POSTGRES_URL`), **10 000** rows, warmup 30 / measure 200:

| Engine | Scenario | P95 | ratio_vs_postgres_p95 |
|--------|----------|-----|------------------------|
| lidb | no index | **0.25 ms** | **0.36×** |
| lidb | with index (hash/map) | **0.04 ms** (~**5.7×** vs scan) | **0.12×** |
| postgres | no index | **0.71 ms** | — |
| postgres | with index (btree) | **0.39 ms** (~**1.8×** vs scan) | — |

Source: [`results/latest.json`](results/latest.json) (`postgres: true`). Do not market these numbers as CI-gated Supabase parity — PH-DB-7 owns pass/fail thresholds later.

## Run

```powershell
$env:LIDB_ROOT = "C:\Users\Julian\Documents\Programming\li\lidb"
$env:LIDB_EMBED = "$env:LIDB_ROOT\build\smoke\Release\lidb_embed.exe"
$env:POSTGRES_URL = "postgresql://postgres:postgres@127.0.0.1:5432/postgres"
python benchmarks/oltp-compare/run_compare.py --rows 10000 --warmup 30 --measure 200
```

## CI

Record-only workflow: [`.github/workflows/oltp-compare.yml`](../../.github/workflows/oltp-compare.yml) (`workflow_dispatch` / nightly). Uploads `latest.json` as an artifact; does **not** fail on ratio. Skips honestly (exit 0) when `lidb_embed` is unavailable.
