# Plan loop: Supabase-parity deepen remainders

**Worker:** `librebase-parity-deepen` (li-swarm)  
**Branches:** librebase `feat/deepen-phase1-auth-storage-mcp` · lis `feat/deepen-phase1-refresh-buckets`

## Todos

- id: smtp-email
  content: Lean SMTP/mock path for magiclink OTP; tests; DEEPEN auth_smtp
  status: pending
- id: sigv4-full
  content: Deepen storage SigV4 beyond shaped MVP; tests; DEEPEN storage_sigv4
  status: pending
- id: cdn-image
  content: Lean image transform or honest OOS; DEEPEN cdn_image
  status: pending
- id: playwright-or-defer
  content: Playwright browser E2E or keep deferred_lean with justification
  status: pending
- id: mcp-close-gaps
  content: Cheap MCP gaps toward mcp_full_supabase; stay lean
  status: pending
- id: deepen-done
  content: DEEPEN.json status=done + push lis MR !161 + librebase PR #20
  status: pending

## DoD

1. `bash scripts/check-deepen-remainders-gate.sh` exits 0
2. Tracker `status=done` with honest note (no fake green)
3. lis + librebase branches pushed
