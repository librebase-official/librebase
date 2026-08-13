# Librebase benchmark video — "Every dimension, one table" (vector, finally won)

Follows the same structure and honesty rules as
`docs/demo/librebase-vision-video-script.md`. This cut is the **full benchmark**
across all tested functionality dimensions, head-to-head against Supabase on
the same Mac — with the headline that the last remaining gap, **vector search**,
is now closed and Librebase wins it by ~9× at equal accuracy.

Measured data sources:
- Vector: fresh run, `benchmarks/full-stack/results/vector-fresh-2026-08-13.json`
  (this session, Li HNSW engine, hnswlib-faithful).
- All other dimensions: `benchmarks/full-stack/results/*.json` (recorded
  2026-08-11/12, same methodology, same machine).

**Record tooling:** `docs/demo/benchmark-video/storyboard.html` — clickable beat
board that opens the quoted result files.

## Record today in under 20 minutes

| Step | Time | Action |
|------|------|--------|
| 1 | 3 min | Bring up lis + Supabase full; run `scripts/bench_compare.py --sweep` to regenerate the vector table live |
| 2 | 1 min | Open `docs/demo/benchmark-video/storyboard.html`; display zoom 100%, dark room, hide notifications |
| 3 | 12–15 min | One take following the beats below; pause ≤2 s on each table |
| 4 | 2 min | Optional trim in QuickTime or `ffmpeg` (1080p) |

---

## 0:00–0:15 — Hook: the benchmark, and the gap that closed

*[Split screen: pgvector query planner on the left, Li vector CLI on the right;
text: "same 10k x 128 corpus", "same 1000 queries", "same Mac"]*

**VO:** "Every database gets measured on the same table: footprint, speed,
accuracy, and — the one that used to end the argument — vector search. Today
every dimension is on one screen, and the vector column is no longer a loss.
It's the biggest win on the board."

**On screen:** "Librebase vs Supabase — full benchmark, same machine."

---

## 0:15–0:40 — The footprint gap (unchanged, still absurd)

*[Screen record: `podman images` + `podman stats` on both stacks]*

**VO:** "Start where we left off. Full Supabase is twelve containers, seven and
a half gigabytes of images, almost two gigabytes of RAM at idle. Librebase is
one container, **8 megabytes on disk, about 2 megabytes resident**, cold-starting
in a quarter of a second."

**On screen:**

| | Images | RAM idle | Containers |
|---|---|---|---|
| Supabase (full) | ~7.5 GB | ~1.85 GB | 12 |
| Supabase Light | ~2.3 GB | ~140 MB | 3 |
| **Librebase** | **8.2 MB** | **~2 MB** | **1** |

---

## 0:40–1:15 — Vector search: the headline

*[Cut to the vector table; highlight the Librebase HNSW row in green]*

**VO:** "Here's the one that used to be a gap — and now it's the headline. Same
10,000 vectors at 128 dimensions, cosine, warm index, the exact same queries
for both engines. Librebase's HNSW at ef=40 answers **4,683 queries per second
at 100% recall**. pgvector, at its own best 100%-recall setting, does **499**.
That's **9.4 times faster at the same accuracy**. And at pgvector's fastest
approximate setting — ef=40 — it only reaches **89% recall**, while Librebase
is at 100% with three times the throughput."

**On screen:**

| engine | QPS | us/query | recall@10 |
|---|---|---|---|
| Librebase exact | 669 | 1495 | 100% |
| **Librebase HNSW ef=40** | **4683** | 214 | **100%** |
| Librebase HNSW ef=320 | 823 | 1214 | 100% |
| pgvector ef=40 | 1129 | 885 | 88.7% |
| pgvector ef=80 | 853 | 1172 | 92.5% |
| pgvector ef=160 | 543 | 1842 | 96.9% |
| pgvector ef=320 | 499 | 2005 | 100% |
| pgvector ef=640 | 488 | 2051 | 100% |

**VO (why):** "pgvector trades recall for speed — it has to. Librebase doesn't:
a faithful HNSW in pure Li, exact-level recall at every ef, with no external
ANN dependency. There is no knob you turn on pgvector that catches it."

---

## 1:15–1:40 — The data plane: ingest + indexed queries

*[Cut to the ingest/index table]*

**VO:** "The rest of the board holds up too. In the 50k-row index benchmark,
Librebase ingests **5,591 rows per second** versus 1,124 through Supabase's
stack, and its indexed point lookup is **0.05 milliseconds** at the session
protocol — roughly **seventy times faster** than Supabase's measured 3.4. Range
and paging land in the same territory."

**On screen:**

| | Supabase | **Librebase** |
|---|---|---|
| Ingest (rows/s) | 1,124 | **5,591** |
| Point lookup p50 | ~3.4 ms | **0.05 ms** |
| Range query p50 | ~15.8 ms | **0.06 ms** |
| LIMIT page p50 | ~3.6 ms | **0.06 ms** |

---

## 1:40–2:05 — REST, Auth, Storage: every op faster

*[Cut to the REST/Auth table, then storage]*

**VO:** "Every REST operation is faster: insert, select, filter, update, delete
at roughly 70–80% of Supabase's latency. Auth is a 4× difference — signup and
login at about a quarter of the time. Storage uploads and gets are 8–10× faster.
Edge functions are the honest wash: Librebase runs a lean interpreter, Supabase
runs Deno."

**On screen:** REST + Auth + Storage p50 table (ratio column).

---

## 2:05–2:25 — Realtime: measured, and one honest gap

*[Cut to realtime; Librebase row filled, Supabase cell dimmed]*

**VO:** "Realtime: Librebase's REST→WebSocket event delivery is measured — 60 of
60 events delivered, p50 of 50 milliseconds. The Supabase cell is left empty,
and that's on purpose: on our bench box the self-hosted Realtime CDC worker
never reaches a connected state, so we don't put a number where we can't
measure one. We show what we measure, and we mark what we don't."

**On screen:**

| Realtime | p50 | delivered |
|---|---|---|
| **Librebase** (REST→WS) | **50 ms** | **60/60** |
| Supabase (CDC) | — (gap) | — |

---

## 2:25–2:40 — Outro: every dimension, one table

*[Librebase logo; the full table scrolls]*

**VO:** "Footprint 900× smaller. Provisioning in a quarter second. Every data
operation faster. And vector search — the category where Postgres had the
clear story — now runs at 100% recall and beats pgvector by **9×**. Same Mac,
same corpus, same queries, one honest table. That's Librebase."

**VO (honest, small):** "Vector numbers are a fresh run with the Li HNSW
engine; all other dimensions are the recorded full-palette run on the same
machine. Supabase-side Realtime event delivery is left as a gap — self-host
CDC bootstrap is blocked on the bench box, not a Librebase result."

---

## Production notes

- **Storyboard:** `docs/demo/benchmark-video/storyboard.html` — clickable beat
  board; links open the result JSONs each beat quotes.
- **Record the vector table live:** `bench_compare.py --sweep` (Li HNSW vs
  pgvector ef sweep, one warm build for Librebase).
- **Honesty rule:** measured numbers only; leave the Supabase Realtime cell
  empty rather than extrapolate.
- Output: `docs/demo/benchmark-video/librebase-benchmark.mp4` (ffmpeg, 1080p).
