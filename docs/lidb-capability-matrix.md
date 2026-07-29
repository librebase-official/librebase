# lidb / Librebase capability matrix

**Status legend:** ⬜ not started · 🚧 in progress · ✅ usable · ❌ out of scope for v1

**Last audit:** 2026-07-29 · Sources: `li/lidb` @ `39853cc`, `li/lis` @ `82da467`, Librebase SDD `docs/sdd/specs/supabase-parity/`, PH-DB status.  
**Pins:** [li-dependency-pins.md](li-dependency-pins.md) · **SDD:** [specs/supabase-parity/](sdd/specs/supabase-parity/) · **Harness:** `scripts/parity_runner.py`

| # | Capability | Supabase reference | Linative home | Status | Notes |
|---|------------|-------------------|---------------|--------|-------|
| 1 | Postgres-shaped SQL | Postgres | **lidb** | 🚧 | INSERT/SELECT in native catalog; CREATE TABLE exec missing — parity uses migration ensure |
| 2 | REST `/rest/v1` | PostgREST | **lis** `routes/rest` | 🚧 | Registry OpenAPI only today; `/rest/v1` scaffold in progress |
| 3 | RLS + JWT | Postgres RLS + GoTrue | **lidb** + **lis** auth | 🚧 | Auth MVP `/v1/auth`; RLS SQL present; engine eval not wired |
| 4 | WAL / durability | Postgres WAL | **lidb** | 🚧 | WAL append on insert; ~75% PH-DB N1 on feature branch |
| 5 | Realtime fanout | Realtime | **lis** `routes/realtime` | 🚧 | Phoenix WS partial; soft P-RT-01 |
| 6 | Object Storage | Storage | **lidb** blob + **lis** | ⬜ | Wave B |
| 7 | Edge Functions | Edge Functions | **li-edge** | 🚧 | Scaffold v0.1.0; Wave B |
| 8 | Connection pooler | Supavisor | **lis** in-process | ⬜ | |
| 9 | Migrations | CLI / Studio | **lidb** + `lis db migrate` | 🚧 | Registry migrations; Studio migrate stub |
| 10 | Backup / restore | Backup | **lis** `db backup` | 🚧 | Not Studio PITR |
| 11 | PITR / branching | Branching | **lidb** | ⬜ | Paid Cloud later |
| 12 | Auth (email/OAuth) | GoTrue | **lis** + **li-oauth** | 🚧 | Email/password MVP; OAuth package scaffold |
| 13 | Logs | Logflare | **li-log** | 🚧 | On lip; not wired into Studio |
| 14 | Analytics | Analytics | future | ⬜ | |
| 15 | API gateway | Kong | **li-httpd** + **lis** | 🚧 | Buildable; not Librebase-composed |
| 16 | Studio console | Dashboard | **Librebase Studio** | 🚧 | Projects/instances; Admin API optional |
| 17 | Client SDK | `@supabase/supabase-js` | **`@librebase/librebase`** | ⬜ | Wave B |

## Product layers (not matrix rows)

| Layer | Name | Status |
|-------|------|--------|
| Operator admin UI | **Librebase Admin** (Studio) | 🚧 |
| Operator admin API | `admin-api/` in librebase | 🚧 |
| Installable CLI | `librebase` lip + `@librebase/cli` npm | 🚧 |
| Agent control | Librebase MCP | 🚧 — adding `parity_run` |

## Honest bottom line

**Parity is not done (0 ✅).** Wave A harness defines contracts; Li packages are edited in sibling repos. Do **not** mark ✅ without green `P-*` tests.
