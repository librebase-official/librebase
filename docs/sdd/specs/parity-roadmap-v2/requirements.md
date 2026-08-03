# Requirements: parity roadmap v2

## Problem

Wave A / gap-close marked matrix DoD met with honesty leftovers, but the product goal is **true Supabase-shaped surface** beyond MVP rows. Simultaneously, **`lic` is moving to self-hosted** builds; new surface must not depend on cloud-only compilers or Python/C++ shortcuts.

## Goals

1. Ordered waves with explicit **self-hosted `lic` gates** and DoDs.
2. Dependency order: engine (RLS/WAL/migrate) → Li REST/Auth → Storage/Edge → pooler/PITR/billing ✅/❌.
3. Coupling: new runtime/API surface = Li-first after gate.
4. Roadmap-only this cycle; implement waves only after explicit pick.

## Non-goals

- Implementing Waves 1–10 in this cycle
- Fake matrix ✅
- Vendoring Li forks into librebase

## Acceptance

- Design committed at `docs/sdd/specs/parity-roadmap-v2/design.md`
- `docs/parity-plan.md` links v2 as authoritative for post–Wave-A surface
- P0-1 restore of emptied trees completed
