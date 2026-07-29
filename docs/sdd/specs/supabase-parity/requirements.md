# Requirements: Supabase parity (core vertical)

## Problem

Librebase aims for Supabase-shaped product parity on the linative stack (lidb + lis + opt-in packages), but the capability matrix shows **0/17 usable** capabilities and CI only exercises Studio metadata plus a **dev runtime stub**. There is no executable conformance suite, so progress cannot be proven and Li dependency gaps cannot be driven by failing contracts. Operators and agents need honest status and a testable path from stub → real `lis db start` for the core data plane.

## User stories

### US-1 — Honest capability status
As a **platform engineer**, I want the capability matrix and dependency pins to reflect live lidb/lis evidence so that I know what is actually blocked upstream versus unfinished in Librebase.

**Acceptance criteria**
- AC-1.1: `docs/lidb-capability-matrix.md` has a **Last audit** date no older than the current sprint and each of the 17 rows cites branch/PR/commit or “not present” evidence.
- AC-1.2: `docs/li-dependency-pins.md` lists required lidb, lis, and relevant opt-in package versions/SHAs plus known blockers and “harness requires ≥” notes.
- AC-1.3: Matrix cells flip to ✅ only when a named automated parity test passes; docs-only emoji counts are never treated as proof of parity.

### US-2 — Core vertical conformance harness
As a **contributor**, I want an automated Wave A suite (SQL, REST, Auth, RLS) so that Li upgrades and Librebase wiring are measured by failing/passing HTTP contracts.

**Acceptance criteria**
- AC-2.1: `tests/parity/` (or equivalent) defines runnable contracts **P-SQL-01**, **P-REST-01**, **P-AUTH-01**, **P-RLS-01** with clear pass/fail output.
- AC-2.2: When `LIDB_ROOT` (and usable `lis`) is **absent**, the runner exits successfully with an explicit **skipped / degraded** result — not a fake pass of production capabilities.
- AC-2.3: When pinned Li deps are present and Wave A is expected to run, failing contracts yield **non-zero** exit and name the failing IDs.
- AC-2.4: **P-RT-01** (Realtime WS) may be marked soft/skip until the lis realtime work lands, without marking matrix Realtime ✅.

### US-3 — Optional CI without forcing Li in default CI
As a **maintainer**, I want default CI to stay green without lidb/lis, and an optional/nightly parity job when Li is available, so that product PRs are not blocked by missing upstream checkouts.

**Acceptance criteria**
- AC-3.1: Default `.github/workflows/test.yml` (or equivalent) does not fail solely because Wave A was skipped for missing Li.
- AC-3.2: An optional `parity-core` (or equivalent) workflow/job can run Wave A when Li deps are configured.
- AC-3.3: Job output distinguishes `skipped`, `passed`, and `failed` for Wave A.

### US-4 — Production local runtime path
As a **Studio operator**, I want local production launches to use `lis db start` (librebase profile when available) when Li is configured, and the stub only when explicitly opted in, so that health status matches reality.

**Acceptance criteria**
- AC-4.1: With `LIDB_ROOT` + `lis` available and without `LIDB_RUNTIME_MODE=dev`, launch uses the real lis/lidb path (not the port-only stub as the default production path).
- AC-4.2: `LIDB_RUNTIME_MODE=dev` remains an explicit opt-in for stub/degraded local development.
- AC-4.3: Status/health APIs never report “running / healthy production” for stub-only listens without indicating degraded/dev mode.

### US-5 — Agent-visible parity controls
As an **agent or CLI user**, I want MCP/CLI to report pins and harness results (not only markdown emoji tallies) so that I can drive setup and diagnose parity without the Studio GUI.

**Acceptance criteria**
- AC-5.1: MCP and/or CLI can show matrix summary **and** last harness outcome (`not run` | `N pass / M fail` | `skipped`).
- AC-5.2: A `parity_run` (or equivalent) MCP/CLI entry point invokes the harness and returns structured results.
- AC-5.3: Tools listed in the parity plan that are still missing (`list_instances`, `studio_probe`, `runtime_status` or documented successors) are either implemented or explicitly deferred in requirements out-of-scope with a follow-up task.

### US-6 — Upstream Li packages are edited in-tree (sibling checkouts)
As a **platform engineer**, I want Wave A gaps closed by **editing the corresponding Li packages** (lidb, lis, and opt-in li-oauth / li-edge / li-httpd as needed) in their sibling checkouts—not by pin-tracking alone—so that failing harness contracts drive real upstream implementation.

**Acceptance criteria**
- AC-6.1: Each Wave A ID documents which package/path it gates (lidb SQL/WAL, lis REST, lis auth/RLS, lis realtime / profile).
- AC-6.2: Implementation work for failing contracts happens in the Li repos (`Programming/li/lidb`, `Programming/li/lis`, etc.); Librebase then bumps pins and re-runs the harness.
- AC-6.3: Process: implement in Li → bump pin in Librebase → harness green → matrix ✅.
- AC-6.4: Rewriting Admin API from Python to Li is **not** required to mark Wave A green.

## Out of scope

- Full Supabase feature surface (~79 items: Vector, Iceberg analytics buckets, SSO/SAML, branching UI, etc.)
- Wave B: Object Storage S3 API, Edge Functions runtime, `@librebase/librebase` SDK (sequenced after Wave A)
- Connection pooler (Supavisor-shaped), PITR/branching, Analytics product
- Stripe / subscription billing
- Relicensing the entire historical tree in this requirements pass (constitution targets **MIT** for new first-party work; bulk relicense is a separate change)
- Claiming v1.0.0 before remaining matrix rows are ✅ or honest ❌

## Open questions

- None blocking specify→plan: Li checkouts are assumed via `LIDB_ROOT` / `PATH` as today; exact pin SHAs are filled in Phase 0 audit during implementation.
