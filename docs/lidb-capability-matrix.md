# lidb / Librebase capability matrix

**Status legend:** ⬜ not started · 🚧 in progress · ✅ usable · ❌ out of scope for v1

**Last audit:** 2026-08-03 · Sources: `lic` @ `1a466a6` (self-host stage0 built), `li/lidb` @ `9aa11e7` (`feat/wave-1-engine-rls`), `li/lis` @ `723cc95` · **Roadmap:** [parity-roadmap-v2](sdd/specs/parity-roadmap-v2/)  
**Pins:** [li-dependency-pins.md](li-dependency-pins.md) · **Harness:** `scripts/parity_runner.py`  
**Testing honesty:** Wave A = HTTP + embed smoke/pytest. Wave 1 engine RLS = lidb session `set_claims` pytest. Storage/functions = lis unit tests. **Not** native Li `lit` in lidb yet.

| # | Capability | Supabase reference | Linative home | Status | Notes |
|---|------------|-------------------|---------------|--------|-------|
| 1 | Postgres-shaped SQL | Postgres | **lidb** | ✅ | Wave A INSERT/SELECT (P-SQL-01). Minimal `CREATE TABLE` @ `07e816b`. Single-col `CREATE INDEX` hash/map @ `e9f8570` (not B-tree) |
| 2 | REST `/rest/v1` | PostgREST | **lis** `routes/rest` | ✅ | GET/POST/PATCH/DELETE `parity_items` (lidb UPDATE/DELETE @ `9c928eb` + lis wire). Memory PATCH smoke green |
| 3 | RLS + JWT | Postgres RLS + GoTrue | **lidb** + **lis** auth | 🚧 | JWT + lis Python RLS (Wave A). **Engine eval** landed lidb `9aa11e7` (`set_claims` session); lis `LI_RLS_ENGINE=1` wire follow-up |
| 4 | WAL / durability | Postgres WAL | **lidb** | ✅ | WalReader + empty-`catalog.heap` crash-replay smoke (`test_wal_crash_replay_restores_insert`). UPDATE/DELETE WAL still stub; append follows catalog persist |
| 5 | Realtime fanout | Realtime | **lis** `routes/realtime` | ✅ | Phoenix `phx_join` (P-RT-01) + REST INSERT `parity_items` → `postgres_changes` (JSONL notify MVP; not native WAL rows yet) |
| 6 | Object Storage | Storage | **lis** `routes/storage` | ✅ | Filesystem MVP PUT/GET/DELETE `/storage/v1/object/{bucket}/{path}` + unit tests. Not S3 (no list/multipart/signed URLs) — Wave 6 |
| 7 | Edge Functions | Edge Functions | **lis** + **li-edge** | ✅ | Echo MVP / optional `LI_EDGE_ROOT` — Wave 7 real runtime |
| 8 | Connection pooler | Supavisor | **lis** in-process | ❌ | **Wave 8 settled:** OOS for v1 — in-process embed; no `li-pool` |
| 9 | Migrations | CLI / Studio | **lidb** + `lis db migrate` | ✅ | Allowlisted CREATE TABLE + single-col INDEX; POLICY/UNIQUE/multi-col → Wave 3 |
| 10 | Backup / restore | Backup | **lis** `db backup` + export | ✅ | Multi-table SQL/COPY allowlist. Not PITR |
| 11 | PITR / branching | Branching | **lidb** | ❌ | **Wave 9 settled:** OOS for v1 / paid Cloud later |
| 12 | Auth (email/OAuth) | GoTrue | **lis** + **li-oauth** | ✅ | `/v1/auth` (P-AUTH-01). GoTrue alias → Wave 5 |
| 13 | Logs | Logflare | **li-log** + Studio | ✅ | Studio `/logs` JSONL tail |
| 14 | Analytics | Analytics | future | ❌ | Out of scope for v1 |
| 15 | API gateway | Kong | **li-httpd** + **lis** | ✅ | Compose stub + smoke |
| 16 | Studio console | Dashboard | **Librebase Studio** | ✅ | Projects/instances + login/admin/logs |
| 17 | Client SDK | `@supabase/supabase-js` | **`@librebase/librebase`** | ✅ | createClient + smoke |

## Product layers (not matrix rows)

| Layer | Name | Status | Notes |
|-------|------|--------|-------|
| Operator admin UI | **Librebase Admin** (Studio) | ✅ | `/setup`, `/login`, `/admin` members |
| Operator admin API | `admin-api/` in librebase | ✅ | Bearer + entitlements (Wave 10 gates on create/launch) |
| Installable CLI | `librebase` lip + `@librebase/cli` npm | ✅ | smoke |
| Agent control | Librebase MCP | ✅ | `parity_run` + `matrix_status` |

## Honest bottom line

Wave A green; Wave 0 self-host `lic` stage0 built @ `1a466a6`; Wave 1 engine RLS in lidb @ `9aa11e7` (MR open). Waves 8–9 honest ❌. Remaining Li-coupled surface: W2–W7 + W10 entitlement smoke + lis engine wire. Do **not** claim Supabase replacement.
