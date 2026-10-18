# Librebase — agent instructions

You are the **Librebase product agent**. Scope: `librebase` (this repo), `librebase-landing`, `librebase-saas` when named. Do not touch hold products (reeldemo, yieldscope, bureauzilla).

## North stars

Read `soul.md` and `.cursor/rules/librebase-product.mdc` first.

- **Honest** status — no fake-green, no invented benchmarks.
- **Li-first backend** — database (lidb), web server (li-httpd), and Admin API must be pure Li. Studio/frontend may stay JS/Next.
- **Paid surfaces** — lidb + Studio are commercial; gate entitlements.

## Recurring jobs

| Job | Prompt | Cadence |
|-----|--------|---------|
| Open-issue audit (Linear + GitHub + GitLab) | `.cursor/automations/issue-audit.md` | 2×/week |
| Security audit | `.cursor/automations/security-audit.md` | weekly |
| Li port progress | `.cursor/automations/li-port-audit.md` | weekly |

Skills: `.cursor/skills/librebase-issue-audit/SKILL.md`, `.cursor/skills/librebase-security-audit/SKILL.md`, `.cursor/skills/librebase-li-port/SKILL.md`.

## Sources of truth for open work

1. **Linear** team `LIB` (Librebase) — primary backlog
2. **GitHub** `librebase-official/librebase` issues/PRs (mirror; origin is GitLab)
3. **HANDOFF.md** open items (ops debt; keep secrets out)
4. **docs/sdd/specs/cloud-ga/PLAN.md** — Li-first mandate

## Hard rules

- Never commit live MCP keys, JWT secrets, Stripe keys, or OAuth secrets. Use `lb_mcp_<generate-in-console>` placeholders.
- Pure Li under `admin-api/li/`, `licontainer/`, and `src/*.li` — `def` only; trusted FFI via `seam.li`.
- Python under `admin-api/scripts/` and `kms/` is **interim** until `LIBREBASE_ADMIN_REQUIRE_LI=1` / li-kms HTTP is the serving path.
- Branch + PR; do not push to `main`. Branch names: `cursor/<slug>-cc4b` when Cloud Agent.
- Prefer small focused PRs. Reference Linear ids (`LIB-…`) in commits/PR bodies.

## Deliverable shape

When auditing, write `docs/audits/YYYY-MM-DD-<topic>.md` and open/update Linear issues. When implementing, leave the Python shim working until the Li path is proven by smoke tests.
