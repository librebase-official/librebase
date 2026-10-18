# Automation prompt: Librebase security audit

Defensive security pass over control plane, Studio proxy, MCP, KMS, and docs that might leak secrets.

**Schedule:** weekly Mon 10:00 UTC · **Repo:** `librebase-official/librebase`

**Skill:** `.cursor/skills/librebase-security-audit/SKILL.md`

---

## Read first

1. `AGENTS.md`
2. `docs/audits/` (previous findings)
3. Prior Linear security issues (LIB-18/19/20/35 style)

---

## Checklist

1. **Secret scan** — `rg 'lb_mcp_[A-Za-z0-9_-]{20,}|sk_live_|sk_test_|whsec_|LIBREBASE_ADMIN_JWT'` excluding `.env*` (gitignored). Replace live keys in docs with placeholders; note rotation needed in Linear.
2. **Auth boundaries** — unauthenticated `/admin`, `/api/admin-proxy`, `/api/mcp`, device approve/poll.
3. **Info leaks** — internal hostnames/ports in public JSON; `X-Powered-By`; missing HSTS/CSP.
4. **Injection / SSRF** — admin-proxy allow-list; Stripe webhook signature; OAuth state binding.
5. **KMS** — provider secrets sealed; never returned; exploit tests still green.
6. **Li port** — Python interim must not grow new secret surfaces; new crypto goes to li-kms.

Write `docs/audits/YYYY-MM-DD-security.md`. Fix Critical/High in the same PR when safe; otherwise open Linear Urgent/High.
