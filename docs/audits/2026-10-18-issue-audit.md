# Issue audit 2026-10-18

## Summary

Librebase Linear team `LIB` is mostly **Done**. Open work is a small **Competitive**
Backlog (LIB-124…132). GitHub `librebase-official/librebase` has **no open issues**;
open PRs are Dependabot + one CI full-suite PR. Control-plane Li port is the main
engineering gap (Python admin-api interim).

## Linear (open)

| ID | Status | Priority | Title |
|----|--------|----------|-------|
| LIB-124 | Backlog | Medium | Competitive: Convex AI Gateway |
| LIB-125 | Backlog | Low | Competitive: Appwrite Start (India) |
| LIB-126 | Backlog | Low | Competitive: Supabase Logs Ingest pricing |
| LIB-127 | Backlog | Low | Competitive: Appwrite Postgres/MySQL regions |
| LIB-128 | Backlog | Low | Competitive: Supabase OrioleDB beta |
| LIB-129 | Backlog | Low | Competitive: Supabase app MCP / RLS agents |
| LIB-130 | Backlog | Low | Competitive: Supabase acquires Turso |
| LIB-131 | Backlog | Low | Competitive: Neon Realtime public beta |
| LIB-132 | Backlog | Low | Competitive: Clerk MCP server |

In Progress / Todo: **empty**.

## GitHub (open)

- Issues: none listed for `librebase-official/librebase`
- PRs: Dependabot (vitest, types/node, nextjs group) + `ci/full-suite-staging-e2e-security` (#31)

## HANDOFF debt (still relevant)

1. Stripe dashboard webhook URL / price env on VPS
2. Delete endpoints for instances/projects/hosts
3. Upgrade-plan UI in `/admin`
4. Hetzner provisioning Phase 1
5. Instance lifecycle (scheduler, ACME, custom domain)
6. Landing deploy key (not PAT)

## Top actions

1. **Security** — scrub live MCP keys from docs (done this run); rotate keys that appeared in git history.
2. **Li port** — continue `admin-api/li/` after `/health` (setup → auth → org CRUD).
3. **MCP agent discovery** — re-verify live `/.well-known/mcp.json` (HTML 404 claimed Aug 28).
4. Leave Competitive backlog as watch items unless GTM asks for positioning PRs.
5. Triage Dependabot PRs separately from product work.

## Done this run

- Librebase agent kit (`AGENTS.md`, automations, skills)
- Pure-Li Admin scaffold (`admin-api/li/`, `src/seam.li`)
- Security scrub of HANDOFF MCP key placeholder
- Linear: [LIB-133](https://linear.app/librebase/issue/LIB-133) (Li Admin port), [LIB-134](https://linear.app/librebase/issue/LIB-134) (rotate MCP keys), [LIB-135](https://linear.app/librebase/issue/LIB-135)/[LIB-136](https://linear.app/librebase/issue/LIB-136) (setup + auth children)
