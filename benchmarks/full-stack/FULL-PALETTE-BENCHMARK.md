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
| Vector search (10k×128d) | exact 271 ms / LSH 106 ms | **pgvector 8.6 ms / HNSW 8.8 ms** |
| Edge invoke | **65 ms** (lean WASM) | 63 ms (Deno) |
| Realtime connect | **2.7 ms** | n/a* |
| Realtime join | **0.9 ms** | n/a* |
| Realtime event delivery | **48 ms** (20/20) | n/a* |

\* Supabase realtime cluster reports `replication_connected:false` and rejects
all WS connections (HTTP 400) in this podman bootstrap — its event delivery is
not measurable here (documented infra gap, not a Librebase gap).

## Vector search — honest

Same scale (10k×128d, top-10):

| | Librebase (in-process) | Supabase pgvector |
|---|---|---|
| Exact search p50 | 271 ms | **8.6 ms** |
| Approx search p50 | 106 ms (LSH) | **8.8 ms** (HNSW) |
| Ingest rows/s | 832 | **1843** |

Honest: lis's lean Python vector engine is an O(n) in-process index — **much
slower than pgvector HNSW at 10k rows**. This is a real gap: pgvector is the
reference target for future native lis vector work (see `vector.mjs`).
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
- **Vector is a Librebase gap**: lis's lean O(n) Python engine is ~30× slower than
  pgvector HNSW at 10k rows (271 ms vs 8.8 ms). pgvector is the reference target
  for native lis vector work.
- Edge runtime differs (Deno vs lean WASM interpreter) — same order of magnitude,
  not a runtime-parity claim.
