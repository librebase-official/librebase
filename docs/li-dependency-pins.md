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
| lidb | `C:\Users\Julian\Documents\Programming\li\lidb` | `feat/wave-a-parity-export` @ `fb03d42` | `parity_items` bootstrap + export/import |
| lis | `C:\Users\Julian\Documents\Programming\li\lis` | `feat/librebase-parity-wave-a` @ `7e0e4bb` | librebase profile + lidb REST |
| li-oauth | `C:\Users\Julian\Documents\Programming\li-oauth` | `main` @ `92501c6` | Wave B / OAuth |
| li-edge | `C:\Users\Julian\Documents\Programming\li-edge` | `main` @ `2dc7578` | Wave B |
| li-httpd | `C:\Users\Julian\Documents\Programming\li\li-httpd` | `main` @ `3b7472e` | Gateway compose later |

## Harness requires ≥

Wave A (`scripts/parity_runner.py`) needs:

1. `LIDB_ROOT` pointing at a lidb tree that can embed / migrate
2. `lis` on `PATH` (or `LIS_ROOT`) + registry server (or `python routes/registry/server.py`)
3. `LI_PROFILE=librebase`, `LI_JWT_SECRET`, `LIBREBASE_PARITY_API` (default `http://127.0.0.1:54321`; use alternate port if OS-blocked)

Without Li: runner exits **0** with `status: skipped`, `reason: no_lidb` — not a production pass.

**Evidence (2026-07-30):** live run on `:15421` — P-SQL-01, P-REST-01, P-AUTH-01, P-RLS-01 **pass**; P-IO-01/P-RT-01 soft skip. Report: `tests/parity/last-report.json`.

## Known blockers (post–Wave A)

| Contract | Blocker | Home |
|----------|---------|------|
| CREATE TABLE DDL | Not in native catalog exec; bootstrap ensure only | lidb |
| P-RLS engine | Policies enforced in lis Python for Wave A | lidb engine eval |
| P-IO-01 hard | Soft until `PARITY_REQUIRE_IO=1` | librebase + lidb |
| P-RT-01 | Soft; realtime partial | lis |

## Process

1. Implement in Li repo → commit/PR there  
2. Update SHA in this file  
3. `python scripts/parity_runner.py` (with stack up) → matrix ✅ only on pass  
