---
name: librebase-security-audit
description: Defensive security audit for Librebase admin-api, Studio proxies, MCP, KMS, and docs. Use when scanning for secret leaks, auth gaps, or writing security audit reports.
---

# Librebase security audit

## Must scan

```bash
rg -n 'lb_mcp_[A-Za-z0-9_-]{16,}|sk_(live|test)_|whsec_|BEGIN (RSA |OPENSSH )?PRIVATE' \
  --glob '!.git/**' --glob '!**/.venv/**' --glob '!**/node_modules/**'
```

## Auth surfaces

| Path | Expect |
|------|--------|
| `/admin` | redirect/login when unauthenticated |
| `/api/admin-proxy` | no internal hostname leak |
| `/api/mcp` + device approve/poll | auth model documented + enforced |
| Stripe webhook | signature verify before mutate |

## Remediation order

1. Rotate + scrub leaked secrets
2. Close auth/info-leak bugs
3. Add tests that fail if secrets reappear in docs
4. File Linear for anything not fixed in-PR
