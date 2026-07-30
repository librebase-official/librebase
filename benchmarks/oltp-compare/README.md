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

## Latest local sample (aims only)

`feat/wave-b-create-index` @ `e9f8570`, in-process EmbeddedSession, **10 000** rows, warmup 30 / measure 200 (no Postgres URL):

| Engine | Scenario | P95 |
|--------|----------|-----|
| lidb | no index | **0.33 ms** |
| lidb | with index (hash/map) | **0.05 ms** (~**6.7×** vs scan) |

Set `POSTGRES_URL` for side-by-side Postgres btree ratios. Do not market these numbers as CI-gated Supabase parity.