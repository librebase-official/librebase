# Li dependency pins (Librebase — lidb / lis)

**Last audit:** 2026-08-03  
**Rule:** Edit Li packages in sibling checkouts; bump pins here; flip matrix ✅ only after Wave A harness green. Do not vendor forks into librebase.  
**Post–Wave-A:** [parity-roadmap-v2](sdd/specs/parity-roadmap-v2/design.md) — new surface requires **self-hosted `lic` ≥ pin** ([wave-0](sdd/specs/parity-roadmap-v2/wave-0-lic-spine.md)).

## Sibling paths (dev / harness)

| Package | Default path | Env |
|---------|--------------|-----|
| **lic** (self-host) | `../li/lic-parity-w0` | `LIC_ROOT` / `LI_REPO_ROOT` |
| lidb | `../li/lidb` relative to librebase, or absolute below | `LIDB_ROOT` |
| lis | `../li/lis` | `PATH` (`lis` CLI) or `LIS_ROOT` |
| li-oauth | `../li-oauth` | lip later |
| li-edge | `../li-edge` | lip later |
| li-httpd | `../li/li-httpd` | lip / compose later |

**This machine (audit):**

| Dep | Absolute path | Git (branch @ SHA) | Notes |
|-----|---------------|--------------------|-------|
| **lic** | `C:\Users\Julian\Documents\Programming\li\lic-parity-w0` | `main` @ `1a466a6` | Fresh GitLab clone (replaces broken `lic` junction/worktrees). Wave 0 gate: stage0 build + `li-tests/self_host_parity/run_token_parity.sh` |
| lidb | `C:\Users\Julian\Documents\Programming\li\lidb` | `feat/wave-3-migrate-depth` @ `e9abac6` | Wave 3 UNIQUE/multi-col INDEX + POLICY metadata (MR !4) |
| lis | `C:\Users\Julian\Documents\Programming\li\lis` | `feat/wave-5-gotrue-alias` @ `4f6b7c0` | Wave 5 `/auth/v1` GoTrue alias + li-oauth lic gate (MR !154). Includes W4 lis-rest @ `08ecd3e` |
| li-oauth | `C:\Users\Julian\Documents\Programming\li-oauth` | `main` @ `92501c6` | OAuth scaffold |
| li-edge | `C:\Users\Julian\Documents\Programming\li-edge` | `main` @ `2dc7578` | Optional `LI_EDGE_ROOT` invoke |
| li-httpd | `C:\Users\Julian\Documents\Programming\li\li-httpd` | `main` @ `3b7472e` | Compose stub: `deploy/edge/librebase.httpd.toml` |

**lis tip note:** Prefer merging `feat/realtime-changefeed` (`36eef49`) into the functions-echo line so one pin carries both notify + echo.

## Harness requires ≥

Wave A (`scripts/parity_runner.py`) needs:

1. `LIDB_ROOT` pointing at a lidb tree that can embed / migrate
2. `lis` on `PATH` (or `LIS_ROOT`) + registry server (or `python routes/registry/server.py`)
3. `LI_PROFILE=librebase`, `LI_JWT_SECRET`, `LIBREBASE_PARITY_API` (default `http://127.0.0.1:54321`; use alternate port if OS-blocked)

Without Li: runner exits **0** with `status: skipped`, `reason: no_lidb` — not a production pass.

**Evidence (2026-07-30):** live run — all six contracts **pass** (no soft skips): P-SQL-01, P-REST-01, P-AUTH-01, P-RLS-01, P-IO-01, P-RT-01. API `:15421`, WS `:15423`.

## Known follow-ups (honest, not v1 blockers)

Tracked in [parity-roadmap-v2](sdd/specs/parity-roadmap-v2/design.md):

| Contract | Wave | Note | Home |
|----------|------|------|------|
| Engine RLS | W1 | Policies still lis Python until engine claims | lidb |
| Native WAL changefeed rows | W2 | JSONL notify MVP for realtime | lis + lidb |
| Migrate POLICY / UNIQUE / multi-col | W3 | Allowlisted CREATE TABLE + single-col INDEX only | lidb |
| Li REST rewrite | W4 | Python `/rest/v1` MVP | lis |
| GoTrue `/auth/v1` + OAuth | W5 | `/v1/auth` only | lis + li-oauth |
| S3-shaped Storage | W6 | Filesystem MVP | lis |
| Edge real runtime | W7 | Echo MVP | li-edge |
| Pooler | W8 | Matrix ❌ or li-pool | li-pool |
| PITR / branching | W9 | Matrix ❌ or lidb | lidb |
| Billing entitlements | W10 | Studio/Admin gates | librebase |

## Process

1. Implement in Li repo → commit/PR there  
2. Update SHA in this file  
3. `python scripts/parity_runner.py` (with stack up) → matrix ✅ only on pass  
