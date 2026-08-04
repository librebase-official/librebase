# Design: Supabase-parity deepen (Auth / Storage / MCP)

**Date:** 2026-08-04  
**North star:** Full GoTrue / Storage / Supabase-MCP clone (**B**).  
**Sequencing:** Parallel thin slices (**4**), then deepen.  
**Approach:** Hybrid — lis Python HTTP now + `.li`/lic gates; stay **lean in RAM** (no heavy deps, prune refresh rows, filesystem buckets).

## Phase 1 (this loop)

| Slice | Ship | Tests |
|-------|------|-------|
| Auth | `refresh_token` + `grant_type=refresh_token`; rotate hashed refresh (cap/prune) | unittest + smoke + `P-AUTH-03` |
| Storage | Bucket list/create/delete; keep HMAC signed GET | unittest + `P-STO-02` |
| MCP | `execute_sql`, `list_tables`, `list_storage_buckets` | tool smoke; fail closed |
| E2E | Playwright/stack path | Required before claiming client on-par for a slice |

## Later (toward B)

MFA/admin/hooks · SigV4/TUS/CDN · full Supabase MCP tool set · live OAuth providers.

## Honesty

Do not claim Supabase replacement. Matrix notes “deepening.” Failures fail — no soft-pass.

## Tracker

`docs/sdd/specs/parity-roadmap-v2/DEEPEN.json` — loop until `status=done`.
