# lidb / Librebase capability matrix

**Status legend:** ⬜ not started · 🚧 in progress · ✅ usable · ❌ out of scope for v1

**Last audit:** 2026-07-30 · Sources: `li/lidb` @ `07e816b` (`feat/wave-b-wal-ddl`), `li/lis` Wave B storage/edge + REST PATCH, Librebase SDD + gap-close.  
**Pins:** [li-dependency-pins.md](li-dependency-pins.md) · **SDD:** [specs/supabase-parity/](sdd/specs/supabase-parity/) · [wave-a-native-io](sdd/specs/wave-a-native-io/) · **Harness:** `scripts/parity_runner.py`  
**Testing honesty:** Wave A proof = HTTP contracts + lidb embed smoke/pytest. Storage/functions = lis unit tests. **Not** native Li `lit` (lidb has no `.li` sources yet). Constitution: ✅ only with automated test.

| # | Capability | Supabase reference | Linative home | Status | Notes |
|---|------------|-------------------|---------------|--------|-------|
| 1 | Postgres-shaped SQL | Postgres | **lidb** | ✅ | Wave A INSERT/SELECT (P-SQL-01). Minimal `CREATE TABLE name (col TYPE, …)` @ `07e816b` (no PK/CONSTRAINT) |
| 2 | REST `/rest/v1` | PostgREST | **lis** `routes/rest` | ✅ | GET/POST/PATCH/DELETE `parity_items` (lidb UPDATE/DELETE @ `9c928eb` + lis wire). Memory PATCH smoke green |
| 3 | RLS + JWT | Postgres RLS + GoTrue | **lidb** + **lis** auth | ✅ | JWT + lis Python RLS. Engine policy eval not wired |
| 4 | WAL / durability | Postgres WAL | **lidb** | ✅ | WalReader + empty-`catalog.heap` crash-replay smoke (`test_wal_crash_replay_restores_insert`). UPDATE/DELETE WAL still stub; append follows catalog persist |
| 5 | Realtime fanout | Realtime | **lis** `routes/realtime` | ✅ | Phoenix `phx_join` (P-RT-01) + REST INSERT `parity_items` → `postgres_changes` (JSONL notify MVP; not native WAL rows yet) |
| 6 | Object Storage | Storage | **lis** `routes/storage` | ✅ | Filesystem MVP PUT/GET/DELETE `/storage/v1/object/{bucket}/{path}` + unit tests. Not S3 (no list/multipart/signed URLs) |
| 7 | Edge Functions | Edge Functions | **lis** + **li-edge** | 🚧 | `/functions/v1/{name}` wired; invoke via `LI_EDGE_ROOT` else honest 501. Not Deno/WASM |
| 8 | Connection pooler | Supavisor | **lis** in-process | ❌ | Out of scope for v1 — in-process embed; no `li-pool` |
| 9 | Migrations | CLI / Studio | **lidb** + `lis db migrate` | 🚧 | CREATE TABLE unlock @ `07e816b`; SQL files still not applied by engine; Studio stub |
| 10 | Backup / restore | Backup | **lis** `db backup` + export | 🚧 | Registry heap tar; app SQL/COPY round-trip (P-IO-01). Not PITR |
| 11 | PITR / branching | Branching | **lidb** | ❌ | Paid Cloud later / out of scope for v1 |
| 12 | Auth (email/OAuth) | GoTrue | **lis** + **li-oauth** | ✅ | `/v1/auth` signup/login (P-AUTH-01). OAuth / GoTrue alias deferred |
| 13 | Logs | Logflare | **li-log** + Studio | ✅ | Studio `/logs` tails JSONL (`LIBREBASE_ACCESS_LOG` / `LIP_REGISTRY_AUDIT_LOG`); vitest `access-log.test.ts`. Not Logflare |
| 14 | Analytics | Analytics | future | ❌ | Out of scope for v1 |
| 15 | API gateway | Kong | **li-httpd** + **lis** | ✅ | Compose stub `deploy/edge/librebase.httpd.toml` + `scripts/smoke_httpd_stub.mjs`. Not full Kong |
| 16 | Studio console | Dashboard | **Librebase Studio** | ✅ | Projects/instances + `/login` cookie + `/admin` members + `/logs`; `scripts/smoke_studio_surfaces.mjs` |
| 17 | Client SDK | `@supabase/supabase-js` | **`@librebase/librebase`** (`packages/sdk`) | ✅ | createClient + smoke `npm test` |

## Product layers (not matrix rows)

| Layer | Name | Status | Notes |
|-------|------|--------|-------|
| Operator admin UI | **Librebase Admin** (Studio) | ✅ | `/setup`, `/login`, `/admin` members; `smoke_studio_surfaces.mjs` |
| Operator admin API | `admin-api/` in librebase | ✅ | Bearer on org routes; idempotent migrations; `smoke_admin.py` |
| Installable CLI | `librebase` lip + `@librebase/cli` npm | ✅ | smoke `packages/cli` `npm test` |
| Agent control | Librebase MCP | ✅ | `parity_run` + `matrix_status`; smoke `packages/mcp` `npm test` |

## Honest bottom line

Wave A contracts green; Storage + REST PATCH/DELETE + Studio logs/gateway stubs landed; lidb WAL crash-replay smoke + minimal CREATE TABLE @ `07e816b`. Realtime row delivery proven via REST→JSONL notify (native WAL rows follow-up). Still open: migrations SQL-file apply, Edge WASM runtime, backup multi-table. Do **not** claim Supabase replacement.
