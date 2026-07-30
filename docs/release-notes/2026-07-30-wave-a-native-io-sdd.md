# 2026-07-30 — SDD wave-a-native-io + soft P-IO-01

## Summary

Added Spec-Driven Development package for Wave A native testing and SQL/COPY import/export; soft `P-IO-01`; live Wave A required contracts green (2026-07-30 evidence).

## Agent continuation

1. **Read:** `docs/sdd/specs/wave-a-native-io/tasks.md` (all MVP done).
2. **Run:** start lis registry (`LI_PROFILE=librebase`, `LIDB_ROOT`, embed); `LIBREBASE_PARITY_API=http://127.0.0.1:<port> PARITY_FORCE=1 python scripts/parity_runner.py`.
3. **Then:** reopen/merge librebase PR; open GitLab MRs for lidb/lis; hard-gate P-IO-01 if desired.
4. **Blocked on:** CREATE TABLE DDL; engine RLS; human merge of sibling MRs.

## Changed

- `docs/sdd/specs/wave-a-native-io/*`
- `docs/sdd/specs/supabase-parity/analyze.md`
- `docs/lidb-capability-matrix.md` — testing honesty + migrate/backup notes
- `tests/parity/contracts.py` — `P-IO-01` soft skip

## Not changed

- Matrix rows still 🚧 (no fake ✅)
- Landing/marketing copy
- Admin billing / Studio SQL editor stubs

## Breaking

N/A.

## Security

N/A.

## Performance

N/A — 64MB aim unchanged; no measured claim.

## Downstream

Depends on lidb `2026-07-30-wave-a-parity-export` and lis `2026-07-30-rest-lidb-export`.
