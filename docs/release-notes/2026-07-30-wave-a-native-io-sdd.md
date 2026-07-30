# 2026-07-30 — SDD wave-a-native-io + soft P-IO-01

## Summary

Added Spec-Driven Development package for Wave A native testing and SQL/COPY import/export, updated analyze/matrix honesty notes, and soft `P-IO-01` parity contract.

## Agent continuation

1. **Read:** `docs/sdd/specs/wave-a-native-io/{requirements,spec,tasks}.md`.
2. **Run:** `python scripts/parity_runner.py` (expect skip without Li); with Li: set `LIDB_ROOT`/`LIS_ROOT` and start librebase profile.
3. **Then:** bump lidb/lis pins after sibling PRs merge; flip matrix ✅ only when Wave A live-green (T6).
4. **Blocked on:** live stack green (T6); Studio IO UI out of scope.

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
