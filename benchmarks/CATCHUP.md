# Librebase catch-up map — gaps → contracts → benches → status

Tracks the remaining honest gaps between Librebase and full Supabase, the
test contract that proves each, the benchmark that measures it, and current
status. Supersedes ad-hoc "still behind" notes in one place.

Legend: ⬜ not started · 🚧 in progress · ✅ done · ❌ out of scope for v1

## Gap map

| # | Gap | Contract / test | Bench | Artifact | Status |
|---|-----|-----------------|-------|----------|--------|
| G1 | REST update/delete by non-id filter | `P-REST-02` (new) — pass vs live lis | SDK live check: `update/delete().eq(code, ...)` verified on :54325 | `tests/parity/last-report.json` + matrix row 17 | ✅ |
| G2 | WAL durability for UPDATE/DELETE | `test_wal_crash_replay_restores_update/_delete` | durability microbench (crash-kill) | CI log + matrix row 4 | ✅ |
| G3 | Realtime event delivery (REST INSERT → WS) | `P-RT-03` (new) — pass vs live stack | `realtime.mjs` event-delivery on lis | `results/realtime-e2e-lis.json` (60/60, p50 ≈ 50 ms) | ✅ (lis); Supabase side ⬜ (realtime cluster unhealthy — `replication_connected:false`) |
| G4 | Storage depth + fair dual-stack bench | `P-STO-03` (new) — pass live: signed GET round-trip + anon deny | `storage.mjs` dual-stack (STACK=lis\|sb) | `results/storage-e2e-lis.json` + `results/storage-e2e-supabase.json` | ✅ |

**G4 bootstrap fixed 2026-08-11** (Supabase storage was 403 in the podman stack):
1. `GRANT authenticator, service_role, anon, authenticated TO supabase_storage_admin` (unblocked `set_config('role',…)`).
2. Created the canonical storage RLS policies (`service_role all objects/buckets`, `public read`, `authenticated owner`) — the minimal bootstrap had RLS on with zero policies (deny-all).
3. `PGRST_DB_SCHEMAS` += `storage` + `GRANT USAGE`/table grants + `Accept-Profile: storage` for PostgREST.
4. Object-list is **POST** (`/object/list/{bucket}`), not GET.

Dual-stack storage result (60 runs, same script): lis upload p50 ≈ 2.8 ms / get ≈ 2.2 ms; Supabase upload ≈ 24 ms / get ≈ 13 ms.
| G5 | Edge beyond echo | `P-FN-01/02` — pass live: li-edge non-echo + fail-closed probe | `edge.mjs` (lis invoke latency) | `results/edge-e2e-lis.json` (p50 ≈ 140 ms subprocess) + lis functions unit tests | ✅ (li-edge non-echo + bench); Deno/WASM remains OOS |

## Closed / proven (do not reopen)

| Claim | Evidence | Status |
|-------|----------|--------|
| Lean RSS 3.797 MB VmRSS (Linux CI) | GitLab job 99197 / pipeline 27003 @ `2bfbd3c` | ✅ |
| Core point lookup ~0.20× Postgres 16 | `oltp-compare` streak 2026-08-05 | ✅ (hard-gated nightly) |
| Range prefix 0.36× Release | `range-scan-streak.json` | ✅ (hard-gated nightly) |
| HTTP REST 0.60× soft vs PostgREST | `http-streak.json` | ✅ soft |
| Footprint (images / idle RSS) | `footprint-provisioning.json` | ✅ (socials source) |
| Non-id PATCH/DELETE via SDK | `P-REST-02` pass vs live lis (:54325); SDK `update/delete().eq(<non-id>, v)` → `?col=eq.v` | ✅ |

## v2 — OOS items delivered (2026-08-11, 155 tests)

Former v1-OOS capabilities now implemented in `lis` with test suites (see
[docs/sdd/specs/oos-v2/DESIGN.md](../docs/sdd/specs/oos-v2/DESIGN.md)):

| OOS | Capability | Module | Tests |
|-----|-----------|--------|-------|
| OOS-1 | Phone auth (SMS OTP) | `routes/auth` | 15 |
| OOS-2 | Connection pooler | `routes/pooler.py` | 16 |
| OOS-3 | Vector engine | `routes/vector` | 40 |
| OOS-4 | Disk B-tree index | `routes/index` | 22 |
| OOS-5 | Analytics | `routes/analytics` | 18 |
| OOS-6 | PITR / branching | `scripts/lidb_branch.py` | 13 |
| OOS-7 | WASM edge runtime | `routes/edge` | 31 |

Honesty holds: these are lean in-process implementations, not full parity
(pooler ≠ Supavisor, branch ≠ PITR-to-txn, vector ≠ pgvector/HNSW, B-tree ≠
Postgres page B-tree/MVCC, WASM ≠ Deno).

## Out of scope for v1 (superseded by v2)

- Connection pooler (Supavisor-class) — delivered as OOS-2 (in-process)
- PITR / branching — delivered as OOS-6 (snapshot branches)
- Phone auth · Analytics · Deno/WASM Edge — delivered as OOS-1/OOS-5/OOS-7 (lean)
- Vector engine — delivered as OOS-3 (in-process exact + LSH)
- Disk B-tree index — delivered as OOS-4 (on-disk B-tree)
- Remaining honest gaps: full Supabase Realtime/Storage bootstrap; native
  pgvector/HNSW; Postgres page B-tree + MVCC; Deno/npm runtime

## Marketing honesty rules

- `MARKETING_UNLOCK.md` is `UNLOCKED` (rows 1–3 + 5 green). Copy may cite
  measured numbers with the caveats: `sorted_tree` ≠ disk B-tree, Release
  `lidb-engine`, `engine_execjson` session IPC.
- Never invent figures. Cite committed / CI-published PASS artifacts only.
- Do **not** claim full Supabase replacement. Realtime dual-stack parity still
  unmeasured (Supabase realtime cluster unhealthy in the podman stack).

## How to run

```bash
# parity contracts (Wave A + new G-contracts), stack up required
python scripts/parity_runner.py

# OLTP hard gates (nightly)
# .github/workflows/oltp-compare.yml  (core,range_scan_name_prefix; ratio ≤ 1.2)

# full-stack benches
cd benchmarks/full-stack
node ingest-index.mjs   # vs Supabase full
node realtime.mjs       # lis event delivery (G3); Supabase side needs realtime cluster healthy
node vector.mjs         # pgvector baseline (Librebase N/A today)
node storage.mjs        # dual-stack: STACK=lis (LIS_API) or STACK=sb (SB_API + SB_KEY)
```
