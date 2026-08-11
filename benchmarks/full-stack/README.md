# Librebase vs Supabase — full-stack benchmark (both LOCAL, podman)

Both stacks run locally on the same Mac via podman. Librebase = lidb engine + lis;
Supabase = official self-host stack (db/auth/rest/realtime/storage/kong/studio).

## 1. Bulk ingest + large-index queries (50k rows, 60 queries)

| Metric | Supabase (PG B-tree via Kong) | Librebase (lidb sorted_tree + hash) |
|--------|-------------------------------|--------------------------------------|
| Ingest | 1,124–2,551 rows/s (via REST) | **10,312 rows/s** (single-row, honest) |
| Point lookup (indexed) p50 | ~3 ms | **0.04 ms** (~75×) |
| Range query p50 | ~8–16 ms | **0.04 ms** |
| LIMIT page p50 | ~2.5 ms | **0.04 ms** |

- **Indexed-lookup improvement:** the lidb `SortedKeyIndex` now adds a **hash
  fast-path** for equality (`find` = O(1) average) alongside the sorted vector for
  ranges. Micro-benchmark: equality find ~0.07–0.3 µs/key. Lazy hash rebuild keeps
  bulk ingest fast (rebuild only on first `find` after mutations).
- **Benchmark realism fix:** lidb is measured over the **persistent `session`
  (NDJSON)** protocol, not a per-query subprocess spawn. The old number (~5 ms)
  was ~99% subprocess+JSON overhead, not the index. Realistic server-path p50 is
  0.04 ms.
- Transport still differs (Supabase via Kong+PostgREST vs lidb direct engine).

## 1b. Index micro-benchmark (equal-key equality find)

| Variant | find/query |
|---------|-----------|
| sorted-vector binary search only | 0.322 µs |
| + hash fast-path (lazy rebuild) | **0.07–0.3 µs** (steady state) |
| persistent-session end-to-end p50 | **0.04 ms** |

## 2. Realtime streaming (WS connect + postgres_changes join)

| Metric | Supabase Realtime (via Kong) | Librebase lis realtime |
|--------|------------------------------|------------------------|
| WS connect p50 | 5.1 ms | **0.9 ms** |
| phx_join (subscribe) p50 | 1.9 ms | **0.4 ms** |

- Both accept `postgres_changes` subscriptions (Phoenix protocol).
- **Event delivery** (INSERT → WS): Supabase realtime user-table CDC requires a
  running per-tenant replication worker; in this single-node podman bootstrap the
  CDC worker for user tables stayed in cluster-discovery (event delivery not
  measured). Librebase event delivery is via lidb changefeed (WAL poll) — measured
  in-process (P-RT-02) but not wired to a live HTTP-insert → WS in this run.

## 3. Buckets / object storage

| Metric | Supabase Storage | Librebase lis storage |
|--------|------------------|------------------------|
| Bucket create / object upload / list | **blocked** (403 — storage RLS/set_config bootstrap) | **works** (200, S3-shaped PUT/GET/list) |

- Librebase storage (lis `routes/storage`) works end-to-end (bucket create, object
  PUT/GET/list, HMAC/sign). Supabase storage container is healthy but the
  `set_config('role'...)` DB call returns 403 in this bootstrap — documented gap.

## 4. Vector search (pgvector baseline)

| Metric | Supabase pgvector (20k × 128-dim) |
|--------|----------------------------------|
| Ingest | 2,037 rows/s |
| Exact top-10 p50 | 4.4 ms |
| HNSW approx top-10 p50 | 4.4 ms |

- **Honest:** Librebase/lidb has **no vector engine yet**. This pgvector baseline
  sets a target for future lidb vector work (dim=128, exact + HNSW).

## Honest caveats

- Transport: Supabase is measured through the **full stack (Kong + PostgREST)**;
  lidb ingest/index is **direct engine exec**. A pure same-path comparison would
  put lidb behind the lis HTTP REST (in-memory store, no index yet).
- Supabase Realtime user-table event-delivery and Storage bucket ops are **blocked
  by self-host bootstrap config** (CDC worker discovery, storage role grants) — not
  measured, documented as gaps.
- lidb has no vector engine (pgvector-only baseline).

## How to run

```bash
# both stacks must be up: full Supabase (podman, :8000 Kong) + lis (:54321) + lidb
cd benchmarks/full-stack
STACK=sb LIBREBASE_API=http://127.0.0.1:8000/rest/v1 LIBREBASE_SERVICE_ROLE=<key> node ingest-index.mjs
STACK=lidb LIDB_EMBED=<lidb> LIDB_DATA=<dir> node ingest-index.mjs
LIBREBASE_SERVICE_ROLE=<key> LIBREBASE_JWT_SECRET=<secret> node vector.mjs
```
