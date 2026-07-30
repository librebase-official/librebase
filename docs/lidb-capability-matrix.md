# lidb / Librebase capability matrix

**Status legend:** ⬜ not started · 🚧 in progress · ✅ usable · ❌ out of scope for v1

**Last audit:** 2026-07-30 · Sources: `li/lidb`, `li/lis`, Librebase SDD `docs/sdd/specs/supabase-parity/` + [`wave-a-native-io/`](sdd/specs/wave-a-native-io/), PH-DB status.  
**Pins:** [li-dependency-pins.md](li-dependency-pins.md) · **SDD:** [specs/supabase-parity/](sdd/specs/supabase-parity/) · [wave-a-native-io](sdd/specs/wave-a-native-io/) · **Harness:** `scripts/parity_runner.py`  
**Testing honesty:** Wave A proof = HTTP contracts + lidb embed smoke/pytest. **Not** native Li `lit` (lidb has no `.li` sources yet). Constitution: ✅ only with automated test.

| # | Capability | Supabase reference | Linative home | Status | Notes |
|---|------------|-------------------|---------------|--------|-------|
| 1 | Postgres-shaped SQL | Postgres | **lidb** | ✅ | Wave A: ensure `parity_items` + INSERT/SELECT (P-SQL-01 green 2026-07-30). CREATE TABLE exec still missing |
| 2 | REST `/rest/v1` | PostgREST | **lis** `routes/rest` | ✅ | Wave A: `/rest/v1/parity_items` lidb-backed (P-REST-01 green). PATCH/DELETE via lidb pending |
| 3 | RLS + JWT | Postgres RLS + GoTrue | **lidb** + **lis** auth | ✅ | Wave A: JWT + lis Python RLS for `parity_items` (P-RLS-01 green). Engine policy eval not wired |
| 4 | WAL / durability | Postgres WAL | **lidb** | 🚧 | WAL append on insert; ~75% PH-DB N1 on feature branch |
| 5 | Realtime fanout | Realtime | **lis** `routes/realtime` | ✅ | Wave A: Phoenix `phx_join` (P-RT-01 hard). Changefeed row delivery still partial |
| 6 | Object Storage | Storage | **lidb** blob + **lis** | ⬜ | Wave B |
| 7 | Edge Functions | Edge Functions | **li-edge** | 🚧 | Scaffold v0.1.0; Wave B |
| 8 | Connection pooler | Supavisor | **lis** in-process | ⬜ | |
| 9 | Migrations | CLI / Studio | **lidb** + `lis db migrate` | 🚧 | Bootstrap ensure + auth schema; SQL files not applied by engine; Studio stub |
| 10 | Backup / restore | Backup | **lis** `db backup` + export | 🚧 | Registry heap tar; app SQL/COPY round-trip hard-gated (P-IO-01). Not PITR |
| 11 | PITR / branching | Branching | **lidb** | ❌ | Paid Cloud later / out of scope for v1 — not a Wave A–B deliverable; backup/restore (#10) is the v1 path |
| 12 | Auth (email/OAuth) | GoTrue | **lis** + **li-oauth** | ✅ | Wave A: `/v1/auth` signup/login (P-AUTH-01 green). OAuth / GoTrue alias deferred |
| 13 | Logs | Logflare | **li-log** | 🚧 | On lip; not wired into Studio |
| 14 | Analytics | Analytics | future | ❌ | Out of scope for v1 — no Logflare/analytics plane planned before Studio + core data APIs |
| 15 | API gateway | Kong | **li-httpd** + **lis** | 🚧 | Buildable; not Librebase-composed |
| 16 | Studio console | Dashboard | **Librebase Studio** | 🚧 | Projects/instances; `/login` cookie session + `/admin` members; Admin API optional |
| 17 | Client SDK | `@supabase/supabase-js` | **`@librebase/librebase`** (`packages/sdk`) | ✅ | Minimal createClient + `.from().select/insert`, `.auth.signUp/signIn`, `.storage` stubs → `/rest/v1`, `/v1/auth`, `/storage/v1`. Smoke: `packages/sdk` `npm test` |

## Product layers (not matrix rows)

| Layer | Name | Status | Notes |
|-------|------|--------|-------|
| Operator admin UI | **Librebase Admin** (Studio) | 🚧 | `/setup`, `/login` (httpOnly cookie), `/admin` members list |
| Operator admin API | `admin-api/` in librebase | ✅ | Bearer on org routes; idempotent migrations; `admin-api/scripts/smoke_admin.py` |
| Installable CLI | `librebase` lip + `@librebase/cli` npm | ✅ | `--help` + commands; smoke `packages/cli` `npm test` |
| Agent control | Librebase MCP | ✅ | `parity_run` + `matrix_status`; smoke `packages/mcp` `npm test` |

## Honest bottom line

**Wave A contracts all hard-gated and green** (P-SQL/REST/AUTH/RLS/IO/RT) against lis+lidb @ pins — evidence `docs/sdd/specs/wave-a-native-io/parity-evidence-2026-07-30.json`. Full matrix still incomplete (Storage/Edge). SDK scaffold + CLI/MCP smokes exist; do **not** claim Supabase replacement.
