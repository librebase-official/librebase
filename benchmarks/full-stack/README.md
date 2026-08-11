# Librebase vs Supabase — full-stack benchmark (both LOCAL, podman)

Both stacks run locally on the same Mac via podman. Librebase = lidb engine + lis;
Supabase = official self-host stack (db/auth/rest/realtime/storage/kong/studio).

## Tiered methodology (fair comparison)

Storage tiers must not be compared head-to-head. In-memory vs on-disk is one
**cross-tier** comparison, used as research input (see §5), not a win claim.

| Tier | Librebase | Supabase |
|------|-----------|----------|
| **In-memory** (volatile, sandbox) | lis `_STORE` (process dict) | in-memory SQLite |
| **On-disk** (durable) | lis + lidb (WAL + heap files) | Postgres + SQLite file |

## 0. Footprint + provisioning — Supabase vision coverage

| Metric | Supabase (full, 12 ctr) | Supabase Light (db+auth+rest) | **Librebase tiny** |
|--------|------------------------|------------------------------|--------------------|
| Images on disk | ~7.5 GB | ~2.3 GB | **8.2 MB** |
| RAM idle (RSS) | ~1.85 GB | ~140 MB | **~2 MB** |
| Cold start → healthy | seconds | ~442 ms | **~265 ms** |
| Containers | 12 | 3 | **1** |

The Supabase vision (sub-second provisioning, sandbox footprint, PostgREST+Auth
compatible so `@supabase/supabase-js` works as-is, upgrade path to full Supabase)
is covered by Librebase: `createClient` + `auth.signUp` + `signInWithPassword` +
`from().insert/select/eq` all work on the lis surface. See
`docs/demo/librebase-vision-video-script.md` for the video.

The compat claim is now measured against the **official postgrest-js suite** (see
`postgrest-js-suite/`): core Data API 111/111 = Supabase full; full suite 274/350
with the remainder being Postgres-native RPC/spread/explain features.

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

## 5. Cross-tier: in-memory vs on-disk (research input, not a head-to-head)

One memory-vs-disk comparison, used to steer a hybrid design (hot rows in
memory, cold on disk):

- **In-memory (lis `_STORE`)** serves the postgrest-js core Data API at ~5–15 ms
  per op (auth + CRUD + filters + joins) with zero I/O — ideal for the hot set.
- **On-disk (lidb WAL + heap)** gives durability and indexes for cold data;
  Supabase full (Postgres) is the durable reference (350/350 on its own suite).
- **Hybrid insight:** lis's in-memory REST plus lidb's WAL-changefeed means a row
  can be served from the in-memory cache and appended to the WAL for durability —
  the same pattern Postgres uses (shared buffers + WAL), at a fraction of the
  footprint. That is the design direction for a mixed on-disk + in-memory tier.

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

# official postgrest-js suite (see postgrest-js-suite/README.md)
REST_URL=http://127.0.0.1:54325/rest/v1 SEED=1 ./postgrest-js-suite/run-suite.sh -u
REST_URL=http://127.0.0.1:8000/rest/v1 ANON_KEY=<anon> ./postgrest-js-suite/run-suite.sh -u
```
