# lidb / Librebase capability matrix

**Status legend:** ⬜ not started · 🚧 in progress · ✅ usable · ❌ out of scope for v1

**Last audit:** 2026-08-05 · Sources: `lic` @ `1a466a6`, lidb @ `e9abac6` / `23f93ca` / `9aa11e7`, lis @ `feat/deepen-phase1-refresh-buckets`, li-edge @ `708a6fa` · **Roadmap:** [parity-roadmap-v2](sdd/specs/parity-roadmap-v2/) (`status=done`) · **Deepen:** [DEEPEN.json](sdd/specs/parity-roadmap-v2/DEEPEN.json) (`status=done`)  
**Pins:** [li-dependency-pins.md](li-dependency-pins.md) · **Harness:** `scripts/parity_runner.py`  
**Testing honesty:** Wave A = HTTP + embed smoke/pytest. Wave 1 engine RLS = lidb session `set_claims` + lis `LI_RLS_ENGINE=1`. Storage/functions = lis unit tests. Edge = P-FN-01 (`runtime: li-edge`). **Not** native Li `lit` in lidb yet. W4 full Li HTTP REST still blocked on lic P0 httpd — do not fake-green.

| # | Capability | Supabase reference | Linative home | Status | Notes |
|---|------------|-------------------|---------------|--------|-------|
| 1 | Postgres-shaped SQL | Postgres | **lidb** | ✅ | Wave A INSERT/SELECT (P-SQL-01). Minimal `CREATE TABLE` @ `07e816b`. Single-col `CREATE INDEX` (sorted_tree / legacy hash_map — not disk B-tree; see oltp `index_impl`) |
| 2 | REST `/rest/v1` | PostgREST | **lis** `routes/rest` | ✅ | GET/POST/PATCH/DELETE `parity_items` (lidb UPDATE/DELETE @ `9c928eb` + lis wire). Memory PATCH smoke green |
| 3 | RLS + JWT | Postgres RLS + GoTrue | **lidb** + **lis** auth | ✅ | JWT + Python RLS default. **`LI_RLS_ENGINE=1`** → lidb embed `session` + `set_claims` (engine eval, skip Python post-filter). Allowlisted `parity_items` / owner_id |
| 4 | WAL / durability | Postgres WAL | **lidb** | ✅ | WalReader + empty-`catalog.heap` crash-replay smoke (`test_wal_crash_replay_restores_insert`). UPDATE/DELETE WAL still stub; append follows catalog persist |
| 5 | Realtime fanout | Realtime | **lis** `routes/realtime` | ✅ | Phoenix join ✅. Row `record` from lidb @ `23f93ca` + JSONL; P-RT-02 in-process record fanout + contract. Live REST→WS needs stack (same as P-RT-01) |
| 6 | Object Storage | Storage | **lis** `routes/storage` | ✅ | Buckets + HMAC + **SigV4 query GET** (host-bound) + TUS stub. **CDN resize `oos_lean`** — `/render/image` passthrough only |
| 7 | Edge Functions | Edge Functions | **lis** + **li-edge** | ✅ | Wave 7: `scripts/invoke.py` (`runtime: li-edge`) @ `708a6fa` / lis. Echo only with `LI_FUNCTIONS_ECHO=1`. Not Deno/WASM |
| 8 | Connection pooler | Supavisor | **lis** in-process | ❌ | **Wave 8 settled:** OOS for v1 — in-process embed; no `li-pool` |
| 9 | Migrations | CLI / Studio | **lidb** + `lis db migrate` | ✅ | Allowlisted CREATE TABLE + INDEX (incl. UNIQUE + ≤3-col) + POLICY metadata @ `e9abac6`; not full Postgres DDL |
| 10 | Backup / restore | Backup | **lis** `db backup` + export | ✅ | Multi-table SQL/COPY allowlist. Not PITR |
| 11 | PITR / branching | Branching | **lidb** | ❌ | **Wave 9 settled:** OOS for v1 / paid Cloud later |
| 12 | Auth (email/OAuth) | GoTrue | **lis** + **li-oauth** | ✅ | Password + refresh + OAuth + MFA + admin + magiclink + **lean SMTP** (`LI_SMTP_MOCK` outbox / `LI_SMTP_*` smtplib). Phone OOS |
| 13 | Logs | Logflare | **li-log** + Studio | ✅ | Studio `/logs` JSONL tail |
| 14 | Analytics | Analytics | future | ❌ | Out of scope for v1 |
| 15 | API gateway | Kong | **li-httpd** + **lis** | ✅ | Compose stub + smoke |
| 16 | Studio console | Dashboard | **Librebase Studio** | ✅ | Projects/instances + login/admin/logs + **VMs/hosts** (multi-instance per VM, memMb budget) |
| 17 | Client SDK | `@supabase/supabase-js` | **`@librebase/librebase`** | ✅ | createClient + smoke; PATCH/DELETE by any `eq` filter column (non-id) via query-string form |

## Product layers (not matrix rows)

| Layer | Name | Status | Notes |
|-------|------|--------|-------|
| Operator admin UI | **Librebase Admin** (Studio) | ✅ | `/setup`, `/login`, `/admin` members |
| Operator admin API | `admin-api/` in librebase | ✅ | Bearer + entitlements (Wave 10 gates on create/launch) |
| Installable CLI | `librebase` lip + `@librebase/cli` npm | ✅ | smoke |
| Agent control | Librebase MCP | ✅ | Admin/parity + SQL/storage/auth admin tools (fail closed) + **in-memory session auth** (`admin_login` persists token/orgId; `auth_status`/`admin_logout`/`set_project_session`) + **VM hosts** (`create_host`/`list_hosts`/`get_host`, instance placement). Not full ~79-item Supabase MCP set (`done_lean`) |

## Honest bottom line

Wave A green; roadmap waves 0–10 marked done (W4 partial: full Li HTTP REST still blocked on lic P0 httpd). Waves 8–9 + phone + Deno Edge + pooler/PITR/analytics honest ❌. Deepen remainders closed (`auth_smtp`, SigV4 query, `cdn_image=oos_lean`, MCP lean). Realtime **event delivery** (REST INSERT → WS) and Storage depth remain active catch-up (see [CATCHUP.md](../benchmarks/CATCHUP.md)).

**Marketing status: [MARKETING_UNLOCK.md](../benchmarks/oltp-compare/MARKETING_UNLOCK.md) is `UNLOCKED`** — copy may cite measured numbers with the caveats below, but must never invent figures or claim full Supabase replacement.

Measured evidence (all published PASS artifacts linked in the unlock checklist):

| Claim | Measured | Caveat |
|---|---|---|
| Lean RSS | **3.797 MB** VmRSS (Linux CI, GitLab job 99197) | Product framing stays “≤64 MB”; Windows advisory non-authoritative |
| Core point lookup | **~0.20×** Postgres 16 (`point_lookup_with_index`) | `sorted_tree` = in-memory ordered secondary, **not** disk B-tree |
| Range prefix scan | **0.36×** median (`range_scan_name_prefix`) | Release build only; Debug inflated ~1.94× |
| HTTP REST vs PostgREST | soft **0.60×** median max | Soft gate only; Python MVP surface |

Always keep caveats (`sorted_tree` ≠ B-tree, Release `lidb_embed`, `embed_execjson` session IPC) in any speed/RSS claim. Scheduled nightly CI stays the regression guard.
