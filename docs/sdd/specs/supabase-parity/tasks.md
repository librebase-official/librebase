# Tasks: Supabase parity (core vertical)

| ID | Task | Depends | DoD | Status |
|----|------|---------|-----|--------|
| T1 | Write `docs/li-dependency-pins.md` | — | AC-1.2 | done |
| T2 | Re-audit matrix | T1 | AC-1.1, AC-1.3 | done |
| T3 | Update `docs/parity-plan.md` | T2 | SDD linked | done |
| T4 | `tests/parity/` Wave A contracts | — | AC-2.1 | done |
| T5 | `scripts/parity_runner.py` | T4 | AC-2.2, AC-2.3 | done |
| T6 | `.github/workflows/parity.yml` | T5 | AC-3.1–3.3 | local file present; GitHub push needs `workflow` OAuth scope — run harness via `python scripts/parity_runner.py` until then |
| T7 | **lis:** `profiles/librebase.toml` | — | AC-4.1 | done |
| T8 | **lis:** `routes/rest/` `/rest/v1` | T7 | Route exists | done |
| T9 | Librebase `lidb_engine` librebase profile | T7 | AC-4.1–4.3 | done |
| T10 | MCP/CLI parity tools | T5 | AC-5.1–5.3 | done |
| T11 | **lidb:** `011_parity_items.sql` | — | Migration | done |
| T12 | **lis auth:** RLS claims doc | T11 | `RLS_CLAIMS.md` | done |
| T13 | **lidb:** engine RLS eval | T11, T12 | P-RLS-01 native | deferred — lis in-memory RLS for Wave A; engine eval follow-up |
| T14 | `/rest/v1` CRUD vs lidb | T8, T11 | P-REST-01 on live stack | partial — in-memory store; lidb-backed follow-up |
| T15 | sdd-analyze + checklist | T1–T14 | analyze.md | done |
| T16 | Commit/push Librebase + lis + lidb | T15 | remotes updated | done |

**Human gates:** waived (`/loop until done`).

**Deferred:** Wave B; GoTrue alias; lidb CREATE TABLE DDL; Li GPL→MIT; Admin Python→Li; native engine RLS (T13).
