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

## Run

```powershell
$env:LIDB_ROOT = "C:\Users\Julian\Documents\Programming\li\lidb"
# optional:
# $env:POSTGRES_URL = "postgresql://postgres:postgres@127.0.0.1:5432/postgres"
# $env:BENCH_ROWS = "5000"
python benchmarks/oltp-compare/run_compare.py --json-out benchmarks/oltp-compare/results/latest.json
```

CI-ish small run:

```powershell
python benchmarks/oltp-compare/run_compare.py --rows 500 --warmup 5 --measure 50
```
