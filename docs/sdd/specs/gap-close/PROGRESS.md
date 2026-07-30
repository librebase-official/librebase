# Gap-close loop progress

**DoD:** Every row in `docs/lidb-capability-matrix.md` is ✅ (test-backed) or ❌ (honest OOS for v1). Product layers usable with smoke tests.

**Last update:** realtime notify closed

## Closed

| Item | Evidence |
|------|----------|
| PITR / Analytics / Pooler | ❌ |
| Product layers (all) | smokes ✅ |
| Storage / REST PATCH / Logs / Gateway / Studio / SDK | ✅ |
| WAL crash-replay + CREATE TABLE | lidb `07e816b` |
| Realtime REST→`postgres_changes` | lis `36eef49` — pin `0d8c145` |

## In flight

| Track | Target |
|-------|--------|
| SQL-file migration apply | matrix #9 |
| Edge echo fallback | matrix #7 |
| Backup multi-table allowlist | matrix #10 |

## Stop condition

Zero ⬜/🚧 on matrix + product layers all ✅.
