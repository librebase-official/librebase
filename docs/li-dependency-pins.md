# Li dependency pins (Librebase ↔ lidb / lis)

**Last audit:** 2026-07-29  
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
| lidb | `C:\Users\Julian\Documents\Programming\li\lidb` | `feat/wp-j-embed-session-reuse` @ `39853cc` | Prefer merge toward `main` for CI |
| lis | `C:\Users\Julian\Documents\Programming\li\lis` | `main` @ `82da467` | Add `profiles/librebase.toml` + `routes/rest/` |
| li-oauth | `C:\Users\Julian\Documents\Programming\li-oauth` | `main` @ `92501c6` | Wave B / OAuth |
| li-edge | `C:\Users\Julian\Documents\Programming\li-edge` | `main` @ `2dc7578` | Wave B |
| li-httpd | `C:\Users\Julian\Documents\Programming\li\li-httpd` | `main` @ `3b7472e` | Gateway compose later |

## Harness requires ≥

Wave A (`scripts/parity_runner.py`) needs:

1. `LIDB_ROOT` pointing at a lidb tree that can embed / migrate
2. `lis` on `PATH` (or `LIS_ROOT/bin` prepended)
3. Profile **`librebase`** when present (`LI_PROFILE=librebase`); else document fallback `registry-min`

Without Li: runner exits **0** with `status: skipped`, `reason: no_lidb` — not a production pass.

## Known blockers (Wave A)

| Contract | Blocker | Home |
|----------|---------|------|
| P-SQL-01 | CREATE TABLE not in native catalog exec; use migration ensure | lidb |
| P-REST-01 | No `/rest/v1/{table}` (registry `/v1/packages*` only) | lis `routes/rest/` |
| P-AUTH-01 | MVP exists at `/v1/auth/*` | lis (harden claims) |
| P-RLS-01 | Policies in SQL; engine eval not wired | lidb + lis JWT GUCs |
| P-RT-01 | Soft; realtime ~35% | lis `routes/realtime` |

## Process

1. Implement in Li repo → commit/PR there  
2. Update SHA in this file  
3. `python scripts/parity_runner.py`  
4. Update `docs/lidb-capability-matrix.md` ✅ only on green named IDs  

## License note

Librebase first-party target: **MIT** (constitution). lidb/lis/li-* remain **GPL-3.0-or-later** until separately relicensed.
