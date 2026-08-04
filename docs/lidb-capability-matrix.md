# lidb / Librebase capability matrix

**Status legend:** ⬜ not started · 🚧 in progress · ✅ usable · ❌ out of scope for v1

**Last audit:** 2026-08-03 · Sources: `lic` @ `1a466a6`, lidb @ `e9abac6`, lis @ `41bfc69`, li-edge @ `708a6fa` · **Roadmap:** [parity-roadmap-v2](sdd/specs/parity-roadmap-v2/) (`status=done`)  
**Pins:** [li-dependency-pins.md](li-dependency-pins.md) · **Harness:** `scripts/parity_runner.py`  
**Testing honesty:** Wave A = HTTP + embed smoke/pytest. Wave 1 engine RLS = lidb session `set_claims` pytest. Storage/functions = lis unit tests. Edge = P-FN-01 (`runtime: li-edge`). **Not** native Li `lit` in lidb yet.

| # | Capability | Supabase reference | Linative home | Status | Notes |
|---|------------|-------------------|---------------|--------|-------|
| 1 | Postgres-shaped SQL | Postgres | **lidb** | ✅ | Wave A INSERT/SELECT (P-SQL-01). Minimal `CREATE TABLE` @ `07e816b`. Single-col `CREATE INDEX` hash/map @ `e9f8570` (not B-tree) |
| 2 | REST `/rest/v1` | PostgREST | **lis** `routes/rest` | ✅ | GET/POST/PATCH/DELETE `parity_items` (lidb UPDATE/DELETE @ `9c928eb` + lis wire). Memory PATCH smoke green |
| 3 | RLS + JWT | Postgres RLS + GoTrue | **lidb** + **lis** auth | 🚧 | JWT + lis Python RLS (Wave A). **Engine eval** landed lidb `9aa11e7` (`set_claims` session); lis `LI_RLS_ENGINE=1` wire follow-up |
| 4 | WAL / durability | Postgres WAL | **lidb** | ✅ | WalReader + empty-`catalog.heap` crash-replay smoke (`test_wal_crash_replay_restores_insert`). UPDATE/DELETE WAL still stub; append follows catalog persist |
| 5 | Realtime fanout | Realtime | **lis** `routes/realtime` | 🚧 | Phoenix join ✅. lidb changefeed now emits row `record` @ `23f93ca`; lis native poll still falls back when only `payload_bytes` historically — re-pin + live P-RT-02 follow-up |
| 6 | Object Storage | Storage | **lis** `routes/storage` + `packages/lis-storage` | ✅ | Buckets + HMAC + SigV4-shaped + **TUS stub** (`/upload/resumable`). Multipart, `public_read`. ❌ image CDN / full AWS SigV4 |
| 7 | Edge Functions | Edge Functions | **lis** + **li-edge** | ✅ | Wave 7: `scripts/invoke.py` (`runtime: li-edge`) @ `708a6fa` / lis `41bfc69`. Echo only with `LI_FUNCTIONS_ECHO=1`. Not Deno/WASM |
| 8 | Connection pooler | Supavisor | **lis** in-process | ❌ | **Wave 8 settled:** OOS for v1 — in-process embed; no `li-pool` |
| 9 | Migrations | CLI / Studio | **lidb** + `lis db migrate` | ✅ | Allowlisted CREATE TABLE + single-col INDEX; POLICY/UNIQUE/multi-col → Wave 3 |
| 10 | Backup / restore | Backup | **lis** `db backup` + export | ✅ | Multi-table SQL/COPY allowlist. Not PITR |
| 11 | PITR / branching | Branching | **lidb** | ❌ | **Wave 9 settled:** OOS for v1 / paid Cloud later |
| 12 | Auth (email/OAuth) | GoTrue | **lis** + **li-oauth** | 🚧 | Password + refresh + GitHub OAuth + **TOTP MFA** + **admin users** (`/auth/v1/admin/users`, service_role). Hooks / phone / magic-link still deepen-to-B |
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
| Agent control | Librebase MCP | 🚧 | Admin/parity + `execute_sql` / `list_tables` / `list_storage_buckets` (fail closed). Not full Supabase MCP set |

## Honest bottom line

Wave A green; roadmap waves 0–10 marked done (W4 partial: full Li HTTP REST still blocked on lic P0 httpd). Waves 8–9 honest ❌. Follow-ups: lis `LI_RLS_ENGINE` wire, Deno/WASM Edge, SigV4 Storage. Do **not** claim Supabase replacement.
