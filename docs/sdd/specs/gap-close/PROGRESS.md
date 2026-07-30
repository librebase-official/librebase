# Gap-close loop progress

**DoD:** Every row in `docs/lidb-capability-matrix.md` is ✅ (test-backed) or ❌ (honest OOS for v1). Product layers usable with smoke tests.

**Loop started:** 2026-07-30

## Closed

| Item | Evidence |
|------|----------|
| PITR / Analytics / Pooler | Matrix ❌ |
| SDK / CLI / MCP / Admin API | smokes ✅ |
| Storage filesystem MVP | lis `feat/wave-b-storage-edge` + unit tests ✅ |
| REST PATCH/DELETE | lidb `9c928eb` + lis wire ✅ |
| li-httpd compose stub | `deploy/edge/librebase.httpd.toml` 🚧 |

## Still open (⬜/🚧)

| # | Cap | Status | Next |
|---|-----|--------|------|
| 4 | WAL | 🚧 | WalReader + crash replay |
| 7 | Edge | 🚧 | Real invoke / WASM |
| 9 | Migrations | 🚧 | CREATE TABLE then SQL apply |
| 10 | Backup | 🚧 | Multi-table beyond allowlist |
| 13 | Logs | 🚧 | Studio wire |
| 15 | Gateway | 🚧 | Run httpd against stub |
| 16 | Studio | 🚧 | Full operator UX |
| 1 note | CREATE TABLE | — | unlocks #9 |

## Stop condition

Stop loop only when matrix has zero ⬜/🚧 (all ✅ or ❌) and product-layer table is all ✅.
