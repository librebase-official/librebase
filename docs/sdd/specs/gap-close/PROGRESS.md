# Gap-close loop progress

**DoD:** Every matrix row ✅ (test-backed) or ❌ (honest OOS for v1). Product layers all ✅.

**Status: DoD MET — 2026-07-30** · Loop stopped.

## Final matrix

All 17 capability rows are ✅ or ❌. Product layers all ✅.

Last pins: lidb `63bb268` · lis functions-echo `723cc95` (+ realtime `36eef49` to merge) · librebase matrix commits through Edge/Backup `abb7bb0` + migrations flip.

## Honesty leftovers (not open matrix rows)

Tracked as **parity-roadmap-v2** waves (Li-coupled, self-hosted `lic`):

| Leftover | Wave |
|----------|------|
| Engine RLS eval | W1 |
| Native WAL changefeed rows | W2 |
| Migrate POLICY / UNIQUE / multi-col | W3 |
| Li REST rewrite | W4 |
| GoTrue `/auth/v1` + OAuth | W5 |
| S3-shaped Storage | W6 |
| Edge real runtime (not echo) | W7 |
| Pooler | W8 ✅/❌ |
| PITR / branching | W9 ✅/❌ (was ❌) |
| Billing entitlements | W10 |

See [parity-roadmap-v2/design.md](../parity-roadmap-v2/design.md). Do **not** tag `v1.0.0` until every matrix row is ✅ or honest ❌.
