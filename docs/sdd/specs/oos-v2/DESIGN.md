# Librebase v2 — OOS implementation plan

**Date:** 2026-08-11
**Status:** **COMPLETE** — all 7 OOS waves implemented + tested (**155 tests**, target 100+) on `lis` `main`.

Related: [lidb-capability-matrix.md](../../lidb-capability-matrix.md) · [CATCHUP.md](../../../benchmarks/CATCHUP.md) · [parity-roadmap-v2/](../parity-roadmap-v2/) · [li-dependency-pins.md](../../li-dependency-pins.md)

## Principle

Same honesty rule as v1: a matrix row flips to ✅ **only** with automated tests, and every claim is bench-backed where it matters. Each OOS wave lands:
1. Implementation in the owning repo (lis / lidb / librebase harness).
2. A test module covering happy path, auth/deny, error paths, and edge cases.
3. A matrix + CATCHUP status flip with evidence artifact.

## Wave map (OOS items) + test inventory

| # | OOS capability | Owner | Tests (module → count) | Status |
|---|----------------|-------|------------------------|--------|
| OOS-1 | Phone auth (SMS OTP + phone signup) | lis `routes/auth` | `test_auth_phone.py` → 15 | ✅ |
| OOS-2 | Connection pooler (lis in-process) | lis `routes/pooler.py` | `test_pooler.py` → 16 | ✅ |
| OOS-3 | Vector engine (exact + LSH-approx) | lis `routes/vector` | `test_vector.py` → 40 | ✅ |
| OOS-4 | Disk B-tree index | lis `routes/index` | `test_btree.py` → 22 | ✅ |
| OOS-5 | Analytics (request/query events) | lis `routes/analytics` | `test_analytics.py` → 18 | ✅ |
| OOS-6 | PITR / branching | lis `scripts/lidb_branch.py` | `test_lidb_branch.py` → 13 | ✅ |
| OOS-7 | WASM Edge runtime | lis `routes/edge` | `test_wasm.py` → 31 | ✅ |
| | **Total** | | **155** | ✅ |

Each module covers: happy path · auth/RLS gates · invalid input · boundary/edge · concurrency/order · honest skip when the underlying runtime is unavailable.

## Honesty gates per wave

- OOS-1: phone OTP minted + delivered (mock SMS), verified once, second use rejected, expiry.
- OOS-2: N concurrent sessions on a bounded pool, no serialization on a global lock, honest `pooler` capability line.
- OOS-3: exact top-k == brute force; HNSW approx within recall threshold; dims/empty/duplicate cases.
- OOS-4: insert/search/delete on disk B-tree; crash-replay; order-scan; range.
- OOS-5: request events recorded + queryable, no PII leakage, retention cap.
- OOS-6: snapshot → branch → diverge → restore; not-fake PITR (real WAL replay).
- OOS-7: WASM module invoke (echo + arithmetic), fail-closed without runtime, not-Deno honesty.

## Sequencing

OOS-1 → OOS-2 → OOS-3 → OOS-5 → OOS-6 → OOS-4 → OOS-7 (tractable-first; each committed + pushed with its tests).
