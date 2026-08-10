# Librebase vs Supabase — full-stack benchmark (both LOCAL, podman)

Both stacks run locally on the same Mac via podman. Librebase = lidb engine + lis;
Supabase = official self-host stack (db/auth/rest/realtime/storage/kong/studio).

## 1. Bulk ingest + large-index queries (50k rows, 60 queries)

| Metric | Supabase (PG B-tree via Kong) | Librebase (lidb sorted_tree) |
|--------|-------------------------------|------------------------------|
| Ingest | 2,551 rows/s | **42,215 rows/s** (16×) |
| Point lookup (indexed) p50 | **2.6 ms** | 5.9 ms |
| Range query p50 | 8.0 ms | **6.0 ms** |
| LIMIT page p50 | **2.5 ms** | 5.9 ms |

- Supabase numbers go through Kong + PostgREST (full stack); lidb is direct engine
  exec — transport differs. Direct PostgREST (no Kong) Supabase lookup was ~0.9–1 ms.
- lidb index is in-memory sorted_tree (not disk B-tree); ingest is much faster,
  point-lookup slightly slower at this size.

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
