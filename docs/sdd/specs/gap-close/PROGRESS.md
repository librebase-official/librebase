# Gap-close loop progress

**DoD:** Every row in `docs/lidb-capability-matrix.md` is ✅ (test-backed) or ❌ (honest OOS for v1). Product layers usable with smoke tests.

**Loop started:** 2026-07-30 · **Last update:** after WAL/DDL agent

## Closed

| Item | Evidence |
|------|----------|
| PITR / Analytics / Pooler | ❌ |
| Product layers (all) | smokes ✅ |
| Storage / REST PATCH / Logs / Gateway / Studio / SDK | ✅ |
| WAL crash-replay + CREATE TABLE | lidb `07e816b` — matrix pin `d57f61f` |

## In flight

| Track | Agent / branch |
|-------|----------------|
| SQL-file migration apply (#9) | lidb migrate agent |
| Edge echo fallback (#7) + backup allowlist (#10) | lis/lidb agent |
| Realtime REST→WS notify (#5 notes) | lis realtime (uncommitted) |

## Still open until agents land

| # | Cap | Status |
|---|-----|--------|
| 7 | Edge | 🚧 |
| 9 | Migrations | 🚧 |
| 10 | Backup | 🚧 |

## Stop condition

Zero ⬜/🚧 on matrix + product layers all ✅.
