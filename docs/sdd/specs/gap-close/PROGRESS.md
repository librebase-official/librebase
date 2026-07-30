# Gap-close loop progress

**DoD:** Every row in `docs/lidb-capability-matrix.md` is ✅ (test-backed) or ❌ (honest OOS for v1). Product layers usable with smoke tests.

**Loop started:** 2026-07-30

## Closed this session

| Item | Evidence |
|------|----------|
| PITR / Analytics | Matrix ❌ |
| `@librebase/librebase` SDK | `packages/sdk` + smoke ✅ |
| CLI / MCP product layers | smokes ✅ |
| Admin API | Bearer org routes + idempotent migrations + `smoke_admin.py` ✅ |
| Studio login/session/members | `/login`, cookie, `/admin` members 🚧 (UI still partial for matrix #16) |

## In flight (workers)

| Track | Target |
|-------|--------|
| lidb UPDATE/DELETE | Unblock REST PATCH/DELETE |
| lis Storage + Edge MVP | Matrix #6, #7 |

## Still open

| # | Cap | Status |
|---|-----|--------|
| 4 | WAL | 🚧 |
| 8 | Pooler | ⬜ |
| 9 | Migrations | 🚧 |
| 10 | Backup | 🚧 |
| 13 | Logs | 🚧 |
| 15 | Gateway | 🚧 |
| 16 | Studio | 🚧 |

## Stop condition

Stop loop only when matrix has zero ⬜/🚧 (all ✅ or ❌) and product-layer table is all ✅.
