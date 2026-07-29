# Librebase SDD Constitution

Non-negotiable principles for Spec-Driven Development in this repo. Later artifacts (`requirements.md`, `spec.md`, `tasks.md`, code) MUST obey these.

1. **Honest status** — Never fake green health or claim capability ✅ without an automated test (or explicit honest ❌). Degraded modes must say so.
2. **Librebase is product, not a fork** — Studio, Admin API, CLI, MCP live here; **lidb** / **lis** / opt-in Li packages remain upstream linative deps. Improve them via pins + PRs, do not vendor forks.
3. **Monetized surfaces** — lidb and Librebase Studio are commercial-shaped; do not expose paid paths without entitlement/auth gates at UI and API/bridge layers.
4. **Core separable** — Keep open `lis` supervisor/registry separable from the commercial Librebase layer.
5. **Pure Li in licontainer** — `licontainer/` is `.li` only (no Rust/C/Python). Use `def` only; trusted FFI is `extern def` in upstream `seam.li`.
6. **License** — First-party product code: **MIT** (easier for adopters/integrators). Do not introduce GPL-only constraints on new first-party surfaces without an explicit product decision.
7. **Parity is HTTP-contract-first** — Core Supabase vertical is measured by executable conformance (SQL/REST/Auth/RLS), not markdown emoji counts alone.
8. **Instance model** — Support both dedicated (1:1) and shared (1:N) instance→project patterns; Org → Instance → Project hierarchy.
9. **No Admin rewrite as a blocker** — Interim Python Admin API is allowed until li-httpd + lic + lidb land; do not block data-plane parity on rewriting Admin.
10. **v1.0.0 gate** — Tag only when every capability-matrix row is ✅ (test-backed) or honest ❌.

**Artifact layout:** `docs/sdd/specs/<feature>/{requirements.md,spec.md,tasks.md}`. Visual UI notes (if any) go in `design.md` — never put technical plans there.
