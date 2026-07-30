# Gap-close loop progress

**DoD:** Every row in `docs/lidb-capability-matrix.md` is ✅ (test-backed) or ❌ (honest OOS for v1). Product layers usable with smoke tests.

**Loop started:** 2026-07-30 · **Last wake:** 2026-07-30T12:40Z

## Closed

| Item | Evidence |
|------|----------|
| PITR / Analytics / Pooler | Matrix ❌ |
| SDK / CLI / MCP / Admin API / Admin UI | smokes ✅ |
| Storage filesystem MVP | lis unit tests ✅ |
| REST PATCH/DELETE | lidb + lis ✅ |
| Logs file tail | Studio `/logs` + vitest ✅ |
| Gateway compose stub | `smoke_httpd_stub.mjs` ✅ |
| Studio surfaces | `smoke_studio_surfaces.mjs` ✅ |
| WAL crash-replay smoke | lidb `07e816b` `test_wal_crash_replay_restores_insert` ✅ |
| Minimal CREATE TABLE | lidb `07e816b` `test_create_table_allowlisted_shape` ✅ |

## In flight

| Track | Target |
|-------|--------|
| Migrations SQL apply | uses CREATE TABLE unlock |
| lis realtime row delivery | agent |

## Still open (⬜/🚧)

| # | Cap | Status |
|---|-----|--------|
| 7 | Edge | 🚧 |
| 9 | Migrations | 🚧 |
| 10 | Backup | 🚧 |
| 5 note | changefeed delivery | partial under ✅ |

## Stop condition

Stop loop only when matrix has zero ⬜/🚧 (all ✅ or ❌) and product-layer table is all ✅.
