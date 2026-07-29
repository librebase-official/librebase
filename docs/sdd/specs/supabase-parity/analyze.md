# SDD analyze: supabase-parity

**Date:** 2026-07-29

## Aligned

- Constitution MIT + honest tests + edit Li packages ↔ requirements US-6 / spec approach
- Wave A IDs P-SQL-01…P-RLS-01 + soft P-RT-01 in `tests/parity/contracts.py`
- Skip path AC-2.2 / AC-3.1 via `parity_runner` + `test_parity_runner.py`
- Pins doc AC-1.2; matrix re-audit AC-1.1; no fake ✅
- lis `profiles/librebase.toml` + `routes/rest/` + registry dispatch
- lidb `011_parity_items.sql`
- MCP `parity_run`, `list_instances`, `studio_probe`, `runtime_status`; CLI `parity`/`pins`
- `lidb_engine.py` prefers `LI_PROFILE=librebase`

## Drift (non-critical)

| Item | Severity | Notes |
|------|----------|-------|
| P-REST/P-SQL/P-RLS not green end-to-end without running stack | medium | In-memory REST RLS works once registry server up; engine RLS still SQL-only |
| lidb CREATE TABLE still missing | medium | Spec allows migration ensure — documented |
| GoTrue `/auth/v1` vs `/v1/auth` | low | Deferred per spec |
| Li packages still GPL vs Librebase MIT constitution | low | Documented in pins |
| tasks T13–T14 partial | medium | REST scaffold + migration landed; full lidb engine RLS eval still open |

## Gaps

- Full stack integration test with live `lis db start` not run in this session (needs LIDB_ROOT+built embed)
- Thermonuclear review not run (waive or follow-up)
- Bulk relicense of librebase tree to MIT not done (constitution target only)

## Recommended fixes

1. Local: set `LIDB_ROOT` + `LI_JWT_SECRET` + start lis `--profile librebase`, run `parity_runner` until Wave A green
2. Continue lidb native RLS eval (T13) in lidb repo
3. Optional: add lis unit test for `/rest/v1/parity_items` RLS in-memory
