# Li dependency pins (Librebase — lidb / lis)

**Last audit:** 2026-08-10  
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
| lidb | `C:\Users\Julian\Documents\Programming\li\lidb` | `main` @ `920ebda` | Merged to main: P5 sorted_tree CREATE INDEX + prefix range, PH-DB-7 lean RSS, wave-3 migrate depth, wave-2 WAL changefeed, wave-1 engine RLS. OLTP CI hard gate pin |
| lidb (PH-DB-7 footprint) | same checkout | `main` @ `920ebda` | Lean RSS gate + `lidb-bench --profile librebase-lean`; PH-DB-7 merged into main |
| lis | `C:\Users\Julian\Documents\Programming\li\lis` | `main` @ `6268be5` | Merged to main: deepen Phase 1 (refresh + buckets + GitHub OAuth), embed session pool / persistent `set_claims` for RLS, Wave 7 edge. Includes realtime changefeed |
| li-oauth | `C:\Users\Julian\Documents\Programming\li-oauth` | `main` @ `92501c6` | OAuth scaffold |
| li-edge | `C:\Users\Julian\Documents\Programming\li-edge` | `main` @ `7ed02b5` | Merged to main: `scripts/invoke.py` real runtime (Wave 7); set `LI_EDGE_ROOT` or sibling auto-discover |
| li-httpd | `C:\Users\Julian\Documents\Programming\li\li-httpd` | `main` @ `3b7472e` | Compose stub: `deploy/edge/librebase.httpd.toml` |

**lis tip note:** All feature lines merged to `main` — one pin (`main` @ `6268be5`) carries notify + changefeed + echo + edge + deepen Phase 1.

## Footprint / PH-DB-7 (64 MB aim)

| Check | Where | Pin / gate |
|-------|-------|------------|
| OLTP SQL hard gate | [`.github/workflows/oltp-compare.yml`](../.github/workflows/oltp-compare.yml) | lidb @ **`e5d6b00`** (`embed_execjson`, `check_gate.py`) |
| Lean RSS ≤ 64 MB steady | lidb `scripts/smoke.sh` + `lidb-bench --profile librebase-lean` | lidb @ **`e5d6b00`** (PH-DB-7 merged to main) |
| Honesty doc | [lidb `docs/footprint.md`](https://gitlab.lilangverse.xyz/li-langverse/lidb/-/blob/main/docs/footprint.md) | Targets are **aims** until PH-DB-7 CI publishes green RSS rows |
| Marketing unlock | [`benchmarks/oltp-compare/MARKETING_UNLOCK.md`](../benchmarks/oltp-compare/MARKETING_UNLOCK.md) | Requires measured RSS **or** keep “64 MB aim” copy forever |

**Linux-only:** PH-DB-7 RSS sampling uses `/proc` (or macOS `ps`) inside lidb — run on Ubuntu CI or Linux VM; Windows dev can document pin + workflow path without local green RSS. Registry-min **256 MB** gate remains the interim engineering ceiling per [product rules](../.cursor/rules/librebase-product.mdc).

## Harness requires ≥

Wave A (`scripts/parity_runner.py`) needs:

1. `LIDB_ROOT` pointing at a lidb tree that can embed / migrate
2. `lis` on `PATH` (or `LIS_ROOT`) + registry server (or `python routes/registry/server.py`)
3. `LI_PROFILE=librebase`, `LI_JWT_SECRET`, `LIBREBASE_PARITY_API` (default `http://127.0.0.1:54321`; use alternate port if OS-blocked)

Without Li: runner exits **0** with `status: skipped`, `reason: no_lidb` — not a production pass.

**Evidence (2026-08-10):** live run on merged main — **12 pass / 0 fail**, one honest skip (P-AUTH-04, GitHub OAuth — needs `PARITY_OAUTH=1` + live secrets). P-SQL-01, P-REST-01, P-AUTH-01..03, P-STO-01/02, P-FN-01 (li-edge), P-RLS-01, P-IO-01 (export/import), P-RT-01/02. API `:54321`, WS `:54323`. See [`tests/parity/last-report.json`](../tests/parity/last-report.json).

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
| Edge real runtime | W7 | Done — li-edge invoke (not Deno) | li-edge |
| Pooler | W8 | Matrix ❌ or li-pool | li-pool |
| PITR / branching | W9 | Matrix ❌ or lidb | lidb |
| Billing entitlements | W10 | Studio/Admin gates | librebase |

## Process

1. Implement in Li repo → commit/PR there  
2. Update SHA in this file  
3. `python scripts/parity_runner.py` (with stack up) → matrix ✅ only on pass  
