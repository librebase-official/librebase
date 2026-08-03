# SDD analyze: supabase-parity

**Date:** 2026-07-30

## Aligned

- Constitution MIT + honest tests + edit Li packages ↔ requirements US-6 / spec approach
- Wave A IDs P-SQL-01…P-RLS-01 + soft P-RT-01 in `tests/parity/contracts.py`
- Skip path AC-2.2 / AC-3.1 via `parity_runner` + `test_parity_runner.py`
- Pins doc AC-1.2; matrix re-audit AC-1.1; no fake ✅
- lis `profiles/librebase.toml` + `routes/rest/` + registry dispatch
- lidb `011_parity_items.sql` (SQL doc; engine apply still bootstrap — see wave-a-native-io)
- MCP `parity_run`, `list_instances`, `studio_probe`, `runtime_status`; CLI `parity`/`pins`
- `lidb_engine.py` prefers `LI_PROFILE=librebase`

## Related feature SDD

Follow-on: [`../wave-a-native-io/`](../wave-a-native-io/) — live Wave A green, bootstrap `parity_items`, lidb-backed REST, SQL+COPY import/export, honest “no lit yet” testing story.

## Drift (non-critical)

| Item | Severity | Notes |
|------|----------|-------|
| P-REST/P-SQL/P-RLS not green end-to-end without running stack | medium | Tracked in wave-a-native-io T3–T6 |
| lidb CREATE TABLE still missing | medium | Spec allows migration/bootstrap ensure — wave-a-native-io uses bootstrap hardcode |
| GoTrue `/auth/v1` vs `/v1/auth` | low | Deferred per spec |
| Li packages still GPL vs Librebase MIT constitution | low | Documented in pins |
| tasks T13–T14 partial | medium | REST scaffold + migration SQL landed; engine RLS eval still open; REST still in-memory until wave-a-native-io T5 |
| `lis db migrate` does not apply `migrations/*.sql` | medium | Writes rev marker + auth ensure; native migrate is bootstrap-only |
| No app-table export/import | medium | Only registry `lis db backup`; wave-a-native-io T7–T10 |
| Zero `.li` / lit in lidb | medium | Do not claim native Li tests; Wave A = HTTP + embed smoke/pytest |

## Gaps

- Full stack integration test with live `lis db start` not yet green (needs LIDB_ROOT+built embed + T3–T6)
- Thermonuclear review not run (waive or follow-up)
- Bulk relicense of librebase tree to MIT not done (constitution target only)

## Recommended fixes

1. Execute [`../wave-a-native-io/tasks.md`](../wave-a-native-io/tasks.md) T3→T12
2. Continue lidb native RLS eval (supabase-parity T13) after Wave A green
3. Optional: Studio export/download UI after CLI P-IO-01
