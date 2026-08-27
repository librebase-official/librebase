# 2026-07-30 — SDD wave-a-native-io (hard gates)

## Summary

Wave A parity harness has **no soft skips**: P-IO-01 (SQL export/import) and P-RT-01 (Phoenix WS join) are required; live evidence 6/6 pass.

## Agent continuation

1. **Read:** `docs/sdd/specs/wave-a-native-io/`, `tests/parity/contracts.py`.
2. **Run:** registry API + `python routes/realtime/server.py --port <ws>`; set `LIBREBASE_PARITY_API`, `LIBREBASE_PARITY_WS`, `LIDB_ROOT`/`LIDB_ENGINE`; `PARITY_FORCE=1 python scripts/parity_runner.py`.
3. **Then:** human-merge PR #9; open GitLab MRs for lidb/lis.
4. **Blocked on:** CREATE TABLE DDL; engine RLS; sibling MR merges.

## Changed

- `tests/parity/contracts.py` — hard P-IO-01 / P-RT-01
- `scripts/parity_runner.py` — any `fail` or unexpected `skip` fails the run; no `soft` bucket
- Matrix / pins / SDD AC updates

## Not changed

- Storage / Edge / SDK
- Studio IO UI
- Engine RLS eval

## Breaking

Harness no longer ignores P-RT-01 failures. Operators must run realtime WS for green Wave A.

## Security

N/A.

## Performance

N/A.

## Downstream

Requires `websockets` for P-RT-01; lidb-engine for P-IO-01.
