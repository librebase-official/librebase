---
workflow_repo: librebase
branch: feat/deepen-phase1-auth-storage-mcp
lis_branch: feat/deepen-phase1-refresh-buckets
phase: deepen-remainders
worker: librebase-parity-deepen
---

# Supabase-parity deepen — remainders (k8s)

Finish **B-full-clone** leftovers for Auth / Storage / MCP while staying **lean in RAM**.

**Plan loop:** [docs/superpowers/plans/2026-08-04-supabase-parity-deepen-remainders-loop.md](../../docs/superpowers/plans/2026-08-04-supabase-parity-deepen-remainders-loop.md)

**Tracker:** `docs/sdd/specs/parity-roadmap-v2/DEEPEN.json` — set `status=done` only when remainders are shipped **or** honestly marked OOS with evidence.

## Sibling checkout (required)

Worker mounts `/workspace/librebase` (this repo) and `/workspace/lis` (`li-langverse/lis` on GitLab). Implement Auth/Storage HTTP in **lis**; parity contracts, SDK, MCP, Playwright, DEEPEN tracker in **librebase**. Push both branches; open/update MR !161 (lis) and PR #20 (librebase).

## Tasks (order)

1. **SMTP / magiclink email** — lean real-or-mock SMTP path for OTP/magiclink (`LI_SMTP_*` or documented mock); tests green; update matrix + DEEPEN `auth_smtp`.
2. **Full SigV4** — deepen beyond shaped MVP for storage signed GET (canonical request + signature verify); tests; DEEPEN `storage_sigv4`.
3. **Image CDN** — lean resize/transform or honest OOS with matrix note; DEEPEN `cdn_image`.
4. **Playwright browser E2E** — add or keep `deferred_lean` with justification; if deferred, still close tracker only after other remainders done/OOS.
5. **MCP deepen** — close `mcp_full_supabase` gaps that are still cheap (no heavy deps).
6. Update `DEEPEN.json` → `status=done`, honest `note`, commit + push both repos.

## Constraints

- Lean RAM — no heavy CDN/SMTP SDKs; stdlib / thin adapters preferred.
- Do not claim full Supabase drop-in.
- Do not weaken tests; fail closed.
- One focused commit per slice with clear message; release notes on lis per org policy.

## Completion gate

```bash
bash scripts/check-deepen-remainders-gate.sh
```

Run from librebase repo root (`/workspace/librebase` in the pod).
