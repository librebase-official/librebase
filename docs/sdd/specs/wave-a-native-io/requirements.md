# Requirements: Wave A native testing + import/export

## Problem

Supabase-parity Wave A contracts exist but skip without a live stack; lidb migrate does not apply SQL migrations or ensure `parity_items`; lis `/rest/v1` is in-memory; there is no app-table import/export (only registry heap backup). Operators cannot prove Wave A or move data from another Postgres-shaped dump into lidb.

## User stories

### US-1 — Live Wave A proof
As a **contributor**, I want Wave A contracts to pass against a real lis+lidb stack so that matrix ✅ is evidence-backed.

**Acceptance criteria**
- AC-1.1: With `LIDB_ROOT` + `lis` + `LI_PROFILE=librebase`, `python scripts/parity_runner.py` exits 0 with status `passed` for P-SQL-01, P-REST-01, P-AUTH-01, P-RLS-01, P-IO-01, P-RT-01 (no soft skips).
- AC-1.2: Without Li, runner still exits 0 with explicit `skipped` (not fake pass).
- AC-1.3: Matrix rows for SQL/REST/Auth/RLS flip to ✅ only after AC-1.1 evidence; notes cite SHA and report path.

### US-2 — Engine ensure of parity fixture
As a **platform engineer**, I want `parity_items` present after native migrate/ensure so that SQL/REST contracts have a real table.

**Acceptance criteria**
- AC-2.1: After `lidb_embed migrate` (or documented ensure), INSERT/SELECT on `parity_items` works via embed exec.
- AC-2.2: Smoke or pytest covers that round-trip (named test).
- AC-2.3: Docs state whether ensure is bootstrap hardcode vs SQL-file apply (honest).

### US-3 — lidb-backed REST
As a **API consumer**, I want `/rest/v1/parity_items` to read/write lidb, not a process-local dict.

**Acceptance criteria**
- AC-3.1: POST then GET via `/rest/v1/parity_items` persists in the catalog (documented restart behavior).
- AC-3.2: `profiles/librebase.toml` marks `rest_v1` as mvp (not stub) once AC-3.1 holds.
- AC-3.3: P-REST-01 and P-SQL-01 pass against that path.

### US-4 — SQL + COPY import/export
As an **operator**, I want to export and import allowlisted tables as plain SQL and text COPY so I can move fixture/app data without pg_dump custom format.

**Acceptance criteria**
- AC-4.1: `lidb_embed export` writes SQL INSERTs for allowlisted tables; `import` reloads them; SELECT matches.
- AC-4.2: COPY text format round-trips the same allowlist.
- AC-4.3: `lis db export` / `lis db import` wrap the embed commands; docs distinguish from `lis db backup` (registry heap tarball).
- AC-4.4: Unknown tables are refused with a clear error.
- AC-4.5: Librebase harness `P-IO-01` is a **hard** contract (export/import round-trip).

### US-5 — Honest native-Li testing story
As a **maintainer**, I want docs to say how specs are tested today vs when lit exists so we never claim native Li coverage we do not have.

**Acceptance criteria**
- AC-5.1: Matrix/pins note: Wave A = HTTP + embed smoke/pytest; lit deferred until `.li` API.
- AC-5.2: No release note claims “native Li tested” for C++-only surfaces.

## Out of scope

- `pg_dump` / `pg_restore` custom format
- MySQL / SQLite dump converters
- Studio upload/download UI (follow-up)
- Engine RLS eval in C++ (may remain lis-enforced for Wave A with note)
- Full CREATE TABLE SQL execution (bootstrap ensure only for MVP; DDL is follow-up)
- Wave B Storage/Edge/SDK
- Relicensing Li packages

## Open questions

- None blocking — locked in grill-me (2026-07-30).
