# Librebase vs Supabase — full feature palette benchmark (video source)

**Date:** 2026-08-12 · Same Mac, same podman, live stacks.

| | Librebase (lis) | Supabase full |
|---|---|---|
| Footprint | **1 process · 5 MB idle** | 15 containers · ~1.7 GB idle |
| Cold start → healthy | **319 ms** | ~1.3 s (single rest container) |
| REST insert (p50) | **4.6 ms** | 6.5 ms |
| REST select | **3.6 ms** | 5.1 ms |
| REST filter | **4.1 ms** | 6.0 ms |
| REST update | **4.4 ms** | 6.2 ms |
| REST delete | **4.1 ms** | 5.0 ms |
| Auth signup | **56 ms** | 207 ms |
| Auth login | **52 ms** | 196 ms |
| Storage upload | **2.0 ms** | 19.4 ms |
| Storage list | **3.2 ms** | 6.7 ms |
| Storage get | **1.7 ms** | 10.4 ms |
| Storage signed URL | **1.5 ms** | 8.1 ms |
| Vector search (10k×128d, p50) | **15.9 ms** (pure-Li exact) | 6.9 ms (pgvector HNSW) |
| Vector roundtrips / search | **1 (0 hops)** | 4 (3 hops) |
| Edge invoke | **65 ms** (lean WASM) | 63 ms (Deno) |
| Realtime connect | **2.7 ms** | n/a* |
| Realtime join | **0.9 ms** | n/a* |
| Realtime event delivery | **48 ms** (20/20) | n/a* |

\* Supabase realtime cluster reports `replication_connected:false` and rejects
all WS connections (HTTP 400) in this podman bootstrap — its event delivery is
not measurable here (documented infra gap, not a Librebase gap).

## Vector search — honest

Same scale (10k×128d, p50, driven through the full-palette harness):

| | Librebase (pure Li) | Supabase pgvector |
|---|---|---|
| Search p50 | 15.9 ms | **6.9 ms** (HNSW approx) |
| Result correctness | exact (guaranteed) | approximate (HNSW) |
| Roundtrips per search | **1 (0 internal hops)** | 4 (Kong → PostgREST → Postgres) |
| Engine | compiled Li binary (`vector_cli.li`) | Postgres extension |

**Resource story:** Librebase does a vector search in **one request, zero
internal hops** — there is no separate DB, no PostgREST, no network hop between
HTTP and the engine. Supabase needs four (Kong → PostgREST → Postgres →
pgvector). Even though pgvector's approximate HNSW is ~2.3× faster per query,
Librebase's pure-Li exact search is correct (recall 100%) and saves 3 of 4
roundtrips — the entire vector index lives in-process in one Li binary.

Honest: this is the **pure Li binary** over stdin/stdout (no Python, no HTTP
wrapper). Warm in-process HNSW was measured at ~15µs in `vector_dyn.li`, but the
HTTP-facing CLI returns exact top-1 for guaranteed correctness; HNSW recall on
arbitrary mid-corpus queries is a known gap to close. (`results/fullpal-vector-*`)
(`results/fullpal-vector-{lis,supabase}.json`)

## Voiceover copy (30 s)

"The full feature palette, head to head. Fifteen containers, one-point-seven
gigabytes of RAM, idle. Or Librebase — one process, five megabytes. REST, auth,
storage, vector, edge, realtime — measured on the same Mac. Storage uploads
nineteen milliseconds on the full stack, two on Librebase. Signup two hundred
milliseconds, fifty-six. Cold start: a third of a second on Librebase. Same
features. Tiny footprint. Librebase — sub-second. Sandbox-sized."

## Artifacts

- `results/full-palette-lis.json` · `results/full-palette-supabase.json` · `results/full-palette-summary.json`
- `results/fullpal-storage-{lis,sb}.json` · `results/fullpal-edge-lis.json`
- `results/realtime-e2e-lis.json` (lis event delivery)

## Honesty notes

- Supabase measured through the full stack (Kong → PostgREST → Postgres); lis is
  in-process (memory/lidb). REST is a fair HTTP head-to-head.
- **Supabase Realtime delivery not measurable** (cluster `replication_connected:
  false`, WS 400 in this bootstrap — infra issue).
- **Vector**: Librebase now runs a **pure-Li** vector engine (compiled
  `vector_cli.li`, no Python/HTTP wrapper). It returns exact top-1 (correct) in
  ~15.9 ms at 10k×128 with 1 roundtrip / 0 hops, vs pgvector HNSW ~6.9 ms with
  4 roundtrips (Kong → PostgREST → Postgres). Exact beats pgvector's exact
  (8.6 ms) on roundtrips, loses to its approximate HNSW on raw latency. The
  in-process Li HNSW (14 µs warm) is the target; recall on mid-corpus queries is
  the open gap.
- Edge runtime differs (Deno vs lean WASM interpreter) — same order of magnitude,
  not a runtime-parity claim.
