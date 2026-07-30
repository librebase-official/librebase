# Tasks: Wave A native testing + import/export

| ID | Task | Depends | DoD | Status |
|----|------|---------|-----|--------|
| T1 | Write `docs/sdd/specs/wave-a-native-io/{requirements,spec,tasks}.md` | — | Files match AC/spec | done |
| T2 | Update `supabase-parity/analyze.md` + matrix gap notes | T1 | analyze cites this feature; no fake ✅ | done |
| T3 | **lidb:** bootstrap `parity_items` in native migrate; pytest/smoke INSERT/SELECT | T2 | AC-2.1–2.3 | done |
| T4 | **lis:** `db migrate` ensures parity fixture via embed | T3 | migrate leaves table queryable | done |
| T5 | **lis:** lidb-backed `/rest/v1/parity_items`; update librebase profile status | T4 | AC-3.1–3.2 | done |
| T6 | Live `parity_runner` green; pin SHAs; matrix ✅ for Wave A rows | T5 | AC-1.1, AC-1.3 | pending — needs full lis stack run |
| T7 | **lidb:** `export`/`import` SQL for allowlist + round-trip test | T3 | AC-4.1, AC-4.4 | done |
| T8 | **lidb:** COPY format + import path | T7 | AC-4.2 | done (CLI; sql pytest covers round-trip) |
| T9 | **lis:** `db export`/`db import` + docs vs backup | T8 | AC-4.3 | done |
| T10 | **librebase:** `P-IO-01` contract + runner | T9 | AC-4.5 | done (soft skip) |
| T11 | Honesty: matrix note on testing layers; no lit claim | T6 | AC-5.1–5.2 | done |
| T12 | Release notes (librebase + lidb + lis) with Agent continuation | T6,T10,T11 | per li-release-notes | pending |

**Human gates:** SDD accepted 2026-07-30.  
**Deferred:** CREATE TABLE DDL exec; engine RLS (supabase-parity T13); Studio IO UI; pg_dump custom; lit/native Li; matrix ✅ until T6 live green.
