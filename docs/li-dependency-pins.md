# Li dependency pins (Librebase — lidb / lis)

**Last audit:** 2026-07-30  
**Rule:** Edit Li packages in sibling checkouts; bump pins here; flip matrix ✅ only after Wave A harness green. Do not vendor forks into librebase.

## Sibling paths (dev / harness)

| Package | Default path | Env |
|---------|--------------|-----|
| lidb | `../li/lidb` relative to librebase, or absolute below | `LIDB_ROOT` |
| lis | `../li/lis` | `PATH` (`lis` CLI) or `LIS_ROOT` |
| li-oauth | `../li-oauth` | lip later |
| li-edge | `../li-edge` | lip later |
| li-httpd | `../li/li-httpd` | lip / compose later |

**This machine (audit):**

| Dep | Absolute path | Git (branch @ SHA) | Notes |
|-----|---------------|--------------------|-------|
| lidb | `C:\Users\Julian\Documents\Programming\li\lidb` | `feat/wave-b-wal-ddl` @ `07e816b` | WAL crash-replay smoke + minimal CREATE TABLE |
| lis | `C:\Users\Julian\Documents\Programming\li\lis` | `feat/wave-b-storage-edge` @ `54a18af` | storage/functions MVP + REST PATCH/DELETE |
| li-oauth | `C:\Users\Julian\Documents\Programming\li-oauth` | `main` @ `92501c6` | Wave B / OAuth |
| li-edge | `C:\Users\Julian\Documents\Programming\li-edge` | `main` @ `2dc7578` | Wave B invoke via `LI_EDGE_ROOT` |
| li-httpd | `C:\Users\Julian\Documents\Programming\li\li-httpd` | `main` @ `3b7472e` | Compose stub: `deploy/edge/librebase.httpd.toml` |

## Harness requires ≥

Wave A (`scripts/parity_runner.py`) needs:

1. `LIDB_ROOT` pointing at a lidb tree that can embed / migrate
2. `lis` on `PATH` (or `LIS_ROOT`) + registry server (or `python routes/registry/server.py`)
3. `LI_PROFILE=librebase`, `LI_JWT_SECRET`, `LIBREBASE_PARITY_API` (default `http://127.0.0.1:54321`; use alternate port if OS-blocked)

Without Li: runner exits **0** with `status: skipped`, `reason: no_lidb` — not a production pass.

**Evidence (2026-07-30):** live run — all six contracts **pass** (no soft skips): P-SQL-01, P-REST-01, P-AUTH-01, P-RLS-01, P-IO-01, P-RT-01. API `:15421`, WS `:15423`.

## Known blockers (post–Wave A)

| Contract | Blocker | Home |
|----------|---------|------|
| CREATE TABLE DDL | Minimal allowlisted shape in native catalog @ `07e816b`; no PK/CONSTRAINT; migrations/*.sql still not applied | lidb |
| P-RLS engine | Policies enforced in lis Python for Wave A | lidb engine eval |
| Full realtime delivery | Join OK; row fanout / native changefeed incomplete | lis + lidb |
| WAL crash replay | Empty-catalog WalReader smoke ✅ @ `07e816b`; UPDATE/DELETE payloads + WAL-before-persist still open | lidb |

## Process

1. Implement in Li repo → commit/PR there  
2. Update SHA in this file  
3. `python scripts/parity_runner.py` (with stack up) → matrix ✅ only on pass  
