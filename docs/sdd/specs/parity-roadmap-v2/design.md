# Design: Supabase-parity roadmap v2 (Li-coupled, self-hosted `lic`)

**Date:** 2026-08-03  
**Status:** approved §1; full map drafted for roadmap-only cycle  
**Related:** [parity-plan.md](../../../parity-plan.md) · [supabase-parity/](../supabase-parity/) · [wave-a-native-io/](../wave-a-native-io/) · [gap-close/PROGRESS.md](../gap-close/PROGRESS.md) · [lidb-capability-matrix.md](../../../lidb-capability-matrix.md) · [li-dependency-pins.md](../../../li-dependency-pins.md)

## 1. Scope and principles

**Deliverable of this cycle:** ordered wave map + DoDs + self-hosted `lic` gates. No product implementation of later waves until a wave is explicitly selected.

**North star:** True Supabase-shaped surface on linative (`lidb` + `lis` + opt-ins), Librebase as product — measured by HTTP/SQL contracts, not matrix emoji.

**Coupling rule (locked):** Every wave that adds *new* runtime/API surface lands a matching self-hosted `lic` (or `.li` package) milestone **first**. No Python/C++ shortcuts for that new surface. Existing Wave A Python / `lidb_embed` MVP may remain until a dedicated rewrite wave retires it — it is not a license to extend.

**Self-host rule:** All `lic` gates run on the self-hosted compiler path (homelab / GitLab runners / repaired selfhost tree). Improving `lic` is in-band with each wave’s gate.

**Honesty:** Matrix ✅ only with automated tests. Unfinished waves stay 🚧 or honest ❌. Tag `v1.0.0` only when every capability-matrix row is ✅ or ❌ ([CONSTITUTION.md](../../CONSTITUTION.md) §10).

**Monetization:** lidb + Studio remain commercial-shaped; entitlement gates at UI/API before paid surfaces.

## 2. Preconditions (P0) — before Wave 0 product work

| ID | Action | DoD |
|----|--------|-----|
| P0-1 | Restore emptied librebase + lis working trees | Key files non-empty (`matrix`, `pins`, `admin_server.py`, `librebase.toml`, `routes/rest/handlers.py`) |
| P0-2 | Repair or replace broken `lic-selfhost-wt` git worktree | `lic` checkout builds with documented self-host command on homelab or local Linux |
| P0-3 | Pin self-host `lic` SHA in `docs/li-dependency-pins.md` | Pins table has `lic` row + “harness requires ≥” note |
| P0-4 | Re-prove Wave A green (or honest skip) | `python scripts/parity_runner.py` with stack up → 6/6 pass, or skip `no_lidb` |

**P0-1 status:** restored 2026-08-03 via `git checkout --` on librebase + lis.

## 3. Wave contract (every wave)

Each wave is a **vertical Li slice**:

```text
self-hosted lic gate → .li package / API → lidb/lis consume → Librebase harness + matrix flip
```

| Field | Meaning |
|-------|---------|
| **Depends** | Prior waves that must be ✅ or explicit rewrite carve-out |
| **lic gate** | Self-host compile/test that must exit 0 before product code for this surface |
| **Li home** | Package / module that owns the behavior |
| **Product surface** | Supabase-shaped HTTP/SQL/Studio behavior |
| **Harness** | Contract IDs or new tests that gate matrix ✅ |
| **DoD** | Exit criteria for the wave |
| **Not this wave** | Explicit fence |

**Rewrite waves** (R0–R2) retire Python/C++ MVPs; they follow the same contract.

## 4. Ordered waves

### Wave 0 — Self-hosted `lic` spine (compiler)

| | |
|--|--|
| **Depends** | P0 |
| **lic gate** | Self-hosted `lic` builds `lic` (or documented subset) on homelab; CI/job green without cloud-only compiler |
| **Li home** | `lic` |
| **Product surface** | None (enables all later waves) |
| **Harness** | Documented self-host smoke script + pin SHA |
| **DoD** | Pins + matrix note: “parity waves require self-host `lic` ≥ \<SHA\>”; broken worktree fixed |
| **Not this wave** | New Supabase HTTP surfaces |

### Wave 1 — Engine RLS (native policy eval)

| | |
|--|--|
| **Depends** | Wave 0 |
| **lic gate** | Self-host `lic` can build lidb policy/`liq` (or agreed embed path) used by RLS tests |
| **Li home** | **lidb** engine RLS + claims wiring; retire lis-only Python RLS for new paths |
| **Product surface** | JWT claims → row filter on REST/SQL without Python policy interpreter for allowlisted tables |
| **Harness** | Extend P-RLS-01 (or P-RLS-02) to assert engine path; fail if Python fallback used when `LI_RLS_ENGINE=1` |
| **DoD** | Matrix RLS notes “engine eval”; live harness green |
| **Not this wave** | Full Postgres POLICY DDL parser completeness beyond allowlist |

### Wave 2 — WAL durability + native changefeed rows

| | |
|--|--|
| **Depends** | Wave 0; Wave 1 preferred for RLS-aware notify |
| **lic gate** | Self-host build of lidb WAL / notify consumers used in tests |
| **Li home** | **lidb** WAL for INSERT/UPDATE/DELETE; row payloads for changefeed |
| **Product surface** | Realtime `postgres_changes` from WAL rows (not JSONL-only notify MVP) |
| **Harness** | P-RT-02 (new): INSERT via REST → WS event with row fields from WAL path |
| **DoD** | Matrix Realtime + WAL notes updated; crash-replay still green |
| **Not this wave** | PITR / branching |

### Wave 3 — Migrate depth (POLICY / UNIQUE / multi-col index allowlist)

| | |
|--|--|
| **Depends** | Wave 0; Wave 1 for POLICY apply semantics |
| **lic gate** | Self-host build of migrate apply path under test |
| **Li home** | **lidb** SQL migrate allowlist expansion |
| **Product surface** | `lis db migrate` applies allowlisted POLICY/UNIQUE/multi-col INDEX from `migrations/*.sql` |
| **Harness** | lidb pytest + optional P-MIG-01 |
| **DoD** | Matrix Migrations notes match allowlist; no fake “full Postgres DDL” |
| **Not this wave** | Arbitrary DDL / pg_dump custom format |

### Wave 4 — Li REST rewrite (`/rest/v1`)

| | |
|--|--|
| **Depends** | Waves 0–1 (RLS); Wave 2 optional for notify-on-write |
| **lic gate** | Self-host `lic` builds lis-rest (or li-httpd route package) `.li` |
| **Li home** | **lis** REST in Li (or li-httpd handlers); remove Python extension for new tables |
| **Product surface** | PostgREST-shaped CRUD on allowlist; filters/headers per harness |
| **Harness** | P-REST-01 on Li path; fail closed if Python handler still serving when profile flag set |
| **DoD** | Matrix REST notes “Li”; Python REST deprecated or deleted for allowlist |
| **Not this wave** | Full PostgREST feature matrix (RPC, views, all operators) |

### Wave 5 — GoTrue path alias + OAuth depth

| | |
|--|--|
| **Depends** | Wave 0; Wave 4 preferred (same gateway) |
| **lic gate** | Self-host build of **li-oauth** / auth package |
| **Li home** | **lis** auth + **li-oauth** |
| **Product surface** | `/auth/v1/*` alias compatible with supabase-js auth basics; OAuth providers per scope |
| **Harness** | P-AUTH-02 GoTrue alias; keep P-AUTH-01 `/v1/auth` until alias sole path |
| **DoD** | Matrix Auth notes alias; SDK smoke against `/auth/v1` |
| **Not this wave** | Full GoTrue admin API / MFA / hooks |

### Wave 6 — Object Storage S3-shaped API

| | |
|--|--|
| **Depends** | Wave 0; Wave 5 for JWT on private buckets |
| **lic gate** | Self-host build of **lis-storage** / object package in Li |
| **Li home** | **lis** storage Li implementation |
| **Product surface** | S3-ish: list, multipart (MVP), signed URLs (MVP), policy hooks allowlist |
| **Harness** | P-STO-01…n; retire “filesystem only / not S3” as sole story |
| **DoD** | Matrix Storage ✅ with S3-shaped tests; honesty on unsupported ops |
| **Not this wave** | Full AWS S3 compatibility / CDN |

### Wave 7 — Edge Functions real runtime

| | |
|--|--|
| **Depends** | Wave 0 with WASM or Li-native isolate story; Wave 5 auth for invoke |
| **lic gate** | Self-host `lic` + **li-edge** runtime build (no echo-only shortcut for *new* invoke path) |
| **Li home** | **li-edge** + lis `/functions/v1` |
| **Product surface** | Deploy/invoke functions with real runtime (Li or WASM — pick one in wave SDD; document) |
| **Harness** | P-FN-01 real runtime (not `runtime:echo`) |
| **DoD** | Matrix Edge ✅ without echo fallback as default in librebase profile |
| **Not this wave** | Deno npm compatibility / full Supabase Edge API |

### Wave 8 — Connection pooler (or honest ❌)

| | |
|--|--|
| **Depends** | Wave 0; network/async maturity in `lic` |
| **lic gate** | Self-host build of **li-pool** (or decide ❌) |
| **Li home** | **li-pool** / lis in-process policy |
| **Product surface** | Supavisor-like pooling **or** matrix ❌ with rationale |
| **Harness** | P-POOL-01 or documented ❌ |
| **DoD** | Matrix row ✅ or ❌ — no 🚧 forever |
| **Not this wave** | Multi-tenant cloud pooler SaaS |

### Wave 9 — PITR / branching (or honest ❌)

| | |
|--|--|
| **Depends** | Wave 2 (WAL) |
| **lic gate** | Self-host tools for basebackup/restore story in Li |
| **Li home** | **lidb** |
| **Product surface** | Point-in-time restore MVP **or** matrix ❌ (paid Cloud later) |
| **Harness** | P-PITR-01 or ❌ |
| **DoD** | Matrix row settled |
| **Not this wave** | Full Supabase branching UX |

### Wave 10 — Product billing entitlements (Librebase)

| | |
|--|--|
| **Depends** | Waves that expose paid surfaces (especially 6–9) |
| **lic gate** | N/A for Admin Python interim (constitution §9); Li Admin rewrite optional later |
| **Li home** | Librebase `admin-api` + Studio gates (product, not `liorg`) |
| **Product surface** | Plan/license checks before launch/catalog for monetized paths |
| **Harness** | Studio/API tests: unpaid → blocked |
| **DoD** | Monetization gates documented + tested |
| **Not this wave** | Stripe full catalog / tax |

### Rewrite waves (retire interim stack)

| ID | Target | Depends | DoD |
|----|--------|---------|-----|
| R0 | lidb: bootstrap → SQL-file migrate as source of truth | Wave 3 | No hardcode-only `parity_items` bootstrap as sole path |
| R1 | lis realtime: delete JSONL-only notify MVP | Wave 2 | WAL path only |
| R2 | Admin API → Li (li-httpd) | Wave 0 + P0-http maturity | Optional; not blocker for data-plane ✅ |

## 5. Dependency graph

```text
P0 restore/pins/Wave A
  → W0 lic self-host spine
    → W1 engine RLS
      → W2 WAL + changefeed rows
      → W3 migrate depth
      → W4 Li REST
        → W5 GoTrue + OAuth
          → W6 S3 Storage
          → W7 Edge runtime
    → W8 pooler ✅/❌
    → W9 PITR ✅/❌ (after W2)
    → W10 billing gates
  → R0/R1/R2 as scheduled after their deps
```

## 6. Librebase control plane (unchanged role)

Studio, CLI, MCP, `parity_runner`, matrix, pins stay in **librebase**. Each wave updates:

1. Sibling Li PR(s) (GitLab-primary)
2. `docs/li-dependency-pins.md` SHA
3. Harness contracts
4. `docs/lidb-capability-matrix.md` (✅ only on green)
5. Release notes (agent continuation) per repo policy

## 7. Out of scope for this roadmap doc

- Implementing Waves 1–10 in this cycle
- Claiming Supabase replacement
- Analytics (already ❌)
- Bulk relicense of Li packages

## 8. Success for “roadmap-only” cycle

- [x] §1 principles approved
- [x] This design written under `docs/sdd/specs/parity-roadmap-v2/`
- [x] `docs/parity-plan.md` points at v2 map
- [ ] Commit/push + `PROGRESS.json` → `status: done`
- [ ] Human picks **Wave 0** (or next) for a separate implement cycle

## 9. Recommended next implement cycle

**Start at Wave 0** (self-hosted `lic` spine) + finish P0-2/P0-3/P0-4. No new Supabase surface until W0 DoD is green.
