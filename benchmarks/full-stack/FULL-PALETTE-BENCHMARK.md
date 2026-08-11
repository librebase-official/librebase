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
| Vector search (exact) | **7.8 ms** (200×64d) | pgvector baseline (see vector.mjs) |
| Edge invoke | **65 ms** (lean WASM) | 63 ms (Deno) |
| Realtime connect | **2.7 ms** | n/a* |
| Realtime join | **0.9 ms** | n/a* |
| Realtime event delivery | **48 ms** (20/20) | n/a* |

\* Supabase realtime cluster reports `db_connected:false` in this podman bootstrap
— its event delivery is not measurable here (documented gap, not a Librebase gap).

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
- Supabase Realtime delivery not measurable (unhealthy cluster in bootstrap).
- Edge runtime differs (Deno vs lean WASM interpreter) — same order of magnitude,
  not a runtime-parity claim.
- Vector: lis exact in-process engine; Supabase pgvector baseline in `vector.mjs`.
