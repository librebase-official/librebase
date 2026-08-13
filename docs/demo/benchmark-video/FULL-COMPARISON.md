# Librebase vs open stack — full comparison

Same machine. Same methodology. Measured numbers only.

- **Vector:** fresh run 2026-08-13 (`vector-fresh-2026-08-13.json`)
- **All other dimensions:** full-palette run 2026-08-11/12 (`benchmarks/full-stack/results/`)
- Competitor label: **open stack** (Postgres + Auth + REST + storage + vector path as measured)

---

## 1. Footprint + provisioning

| Metric | Open stack (full) | Open stack (light) | **Librebase** |
|--------|-------------------|--------------------|---------------|
| Containers | 12 | 3 | **1** |
| Images on disk | ~7.5 GB | ~2.3 GB | **8.2 MB** |
| RAM idle (RSS) | ~1.85 GB | ~140 MB | **~2 MB** |
| Cold start → healthy | seconds | ~442 ms | **~265 ms** |

---

## 2. Vector search (10k × 128-dim, cosine, warm index)

Same corpus, same 1000 queries, QPS excludes index build and payload I/O.

| Engine | QPS | µs/query | recall@10 | top-1 |
|--------|-----|----------|-----------|-------|
| Librebase exact | 669 | 1495 | 100% | 100% |
| **Librebase HNSW ef=40** | **4683** | **214** | **100%** | **100%** |
| Librebase HNSW ef=80 | 2746 | 364 | 100% | 100% |
| Librebase HNSW ef=160 | 1500 | 667 | 100% | 100% |
| Librebase HNSW ef=320 | 823 | 1214 | 100% | 100% |
| Librebase HNSW ef=640 | 581 | 1721 | 100% | 100% |
| Open stack (pgvector) ef=40 | 1129 | 885 | 88.7% | 88.7% |
| Open stack (pgvector) ef=80 | 853 | 1172 | 92.5% | 92.5% |
| Open stack (pgvector) ef=160 | 543 | 1842 | 96.9% | 96.9% |
| Open stack (pgvector) ef=320 | 499 | 2005 | 100% | 100% |
| Open stack (pgvector) ef=640 | 488 | 2051 | 100% | 100% |

### At equal accuracy (100% recall@10)

| Engine | QPS |
|--------|-----|
| **Librebase HNSW ef=40** | **4683** |
| Librebase exact | 669 |
| Open stack (pgvector) ef=320 | 499 |
| Open stack (pgvector) ef=640 | 488 |

**Headline:** Librebase ~**9.4×** faster than the open stack’s best 100%-recall setting (4683 vs 499 QPS). Librebase holds 100% recall at every ef; the open stack must raise ef (and lose QPS) to match accuracy.

---

## 3. Bulk ingest + indexed queries (50k rows)

| Metric | Open stack | **Librebase** |
|--------|------------|---------------|
| Ingest | 1,124 rows/s | **5,591 rows/s** |
| Point lookup p50 | ~3.4 ms | **0.05 ms** |
| Range query p50 | ~15.8 ms | **0.06 ms** |
| LIMIT page p50 | ~3.6 ms | **0.06 ms** |

---

## 4. REST + Auth (p50)

| Operation | Open stack | **Librebase** | Ratio (LB/OS) |
|-----------|------------|---------------|---------------|
| REST insert | 6.52 ms | **4.63 ms** | 0.71× |
| REST select | 5.10 ms | **3.59 ms** | 0.70× |
| REST filter | 5.95 ms | **4.14 ms** | 0.70× |
| REST update | 6.24 ms | **4.37 ms** | 0.70× |
| REST delete | 4.99 ms | **4.07 ms** | 0.82× |
| Auth signup | 206.8 ms | **56.0 ms** | 0.27× |
| Auth login | 196.1 ms | **52.0 ms** | 0.27× |

---

## 5. Storage + Edge (p50)

| Metric | Open stack | **Librebase** |
|--------|------------|---------------|
| Upload | 24.2 ms | **2.8 ms** |
| Get | 12.6 ms | **2.2 ms** |
| List | 8.8 ms | **4.8 ms** |
| Signed URL | 11.4 ms | **2.0 ms** |
| Edge invoke | 63.5 ms | 65.0 ms* |

\*Librebase = lean interpreter; open stack = Deno-class edge. Near parity, not a win claim.

---

## 6. Realtime

| Metric | Open stack | **Librebase** |
|--------|------------|---------------|
| WS connect p50 | ~5.1 ms | **~1.6 ms** |
| Subscribe (join) p50 | ~1.9 ms | **~0.6 ms** |
| Event delivery p50 | **— (gap)** | **50 ms** (60/60 delivered) |

**Gap:** open-stack Realtime CDC event delivery was not measurable on the bench box (self-host worker never reached connected). Librebase REST→WS delivery is measured. Cell left empty on purpose.

---

## 7. Compat (postgrest-js suite)

| | Full suite | Core Data API |
|---|------------|---------------|
| Open stack (full) | 350/350 | 111/111 |
| **Librebase** | **274/350** | **111/111** (= reference) |

Remainder on Librebase: Postgres-native RPC / explain / spread features not in the lean engine.

---

## Summary

| Dimension | Winner |
|-----------|--------|
| Footprint | **Librebase** (~900× smaller images, ~900× less RAM) |
| Provisioning | **Librebase** (sub-second cold start) |
| Vector (equal 100% recall) | **Librebase** (~9.4× QPS) |
| Ingest + indexes | **Librebase** |
| REST / Auth | **Librebase** |
| Storage | **Librebase** |
| Edge | Tie (different runtimes) |
| Realtime delivery | Librebase measured; open stack **gap** |
| Client compat | Core Data API parity; full suite open stack ahead on PG-native features |

---

## Sources

- `benchmarks/full-stack/results/vector-fresh-2026-08-13.json`
- `benchmarks/full-stack/results/full-palette-summary.json`
- `benchmarks/full-stack/results/footprint-provisioning.json`
- `benchmarks/full-stack/results/ingest-index-*.json`
- `benchmarks/full-stack/results/storage-e2e-*.json`
- `benchmarks/full-stack/results/realtime-e2e-lis.json`
- `benchmarks/full-stack/README.md`
