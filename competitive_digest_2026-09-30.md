# LibreBase Competitive Intelligence — Daily Scan 2026-09-30

> **Automated daily scan** — Hermes cron at 09:00 CEST weekdays. 
Scanned 13 known competitors + 6 discovery queries across 51 search queries.
Confidence scores are coarse heuristics; treat as directional.

## Summary

- **Total findings persisted:** 31
- **Strong impact:** 11
- **New competitor candidates:** 8
- **Coverage gaps:** 1 (Railway — Exa backend error)
- **DB status:** see `librebase_competitive_scan.py --status`

## Key Signals This Run

### 🔴 Critical — Supabase Evals (Jul 31 2026)
Supabase open-sourced `supabase/evals` — a benchmark framework scoring AI coding agents (Claude Code, Codex, OpenCode) on real Supabase tasks. Public benchmark at supabase.com/evals. **This is the agent-eval layer LibreBase needs.** If Supabase becomes the de-facto eval standard for agent-built Postgres apps, LibreBase loses the measurement moat.

### 🔴 Critical — Appwrite 2.0 (Aug 31 2026)
Major generation rewrite: native PostgreSQL engine (no abstraction layer), 5 database types including vector, OAuth 2.1/OpenID Connect, S3 storage API, rebuilt TanStack Console. Direct Supabase competitor with vector DB + OAuth2 — both LibreBase core competencies.

### 🟡 High — Xano Q2 2026 Agent Pivot
Xano Agent replaces Logic Assistant, Developer MCP for external agents, XanoScript GA, CLI GA, workspace knowledge layer for AI agents. Most aggressive no-code-to-agent transition seen. Vector embeddings added (R1.59).

### 🟡 High — Backenly (new competitor, Jul 22 2026)
Autonomous backend platform: Postgres + REST + auth + storage + realtime + functions via MCP. Governed mutation kernel (no raw SQL mutations), MAPE-K autonomy loop, PostgREST data plane, multi-tenant by construction. Apache 2.0 + MIT. **Most direct competitive threat to LibreBase found in this scan.** Only 6 GitHub stars but conceptually very close.

### 🟡 High — Nhost MCP Service (Aug 12 2026)
Open-source Nhost MCP service — deploy and let users interact with any AI agent. OAuth2/OIDC provider, embedded docs for LLMs, PostgreSQL 18.1. Closest LibreBase analog (GraphQL + Postgres + auth + MCP + open source).

### 🟡 High — DYPAI (new competitor)
'First backend platform designed for AI to build on.' 40+ MCP tools, IDE-connected (Cursor, Claude Code, Codex, Windsurf, Antigravity), in-dashboard AI builder. MIT SDK. Needs evaluation: partner or competitor?

### 🟡 High — Nubase / OtterMind (new competitor, Jun 2026)
Open-source AI-native backend (Java/Apache 2.0, 627 stars). Postgres + auth + storage + functions + memory primitive + MCP for Claude Code/Codex. Multi-project isolation. Early stage (v0.1.4) but direct overlap.

### 🟢neutral — Supabase MCP Server v0.8.1 (May 2026)
Official MCP server covering full BaaS stack (8 tool groups, OAuth 2.1, remote + stdio). BYO MCP on Edge Functions + Supabase Auth as OAuth2 provider. Stripe Projects co-design partner. SSH doc server (supabase.sh). Most complete BaaS MCP integration.

### 🟢neutral — PocketBase v0.40.0 (Aug 23 2026)
No MCP/agent story. Active release cadence but pure self-hosted BaaS maintainer momentum. Gap opportunity for LibreBase.

### 🟢neutral — Render new plans (Apr-Aug 2026)
No seat fees, SOC 2/ISO self-serve, per-GB billing. CLI `services create` for agents. Deployment platform, not BaaS.

## DB Status
DB: /Users/julian/Documents/coding-projects/librebase/librebase_competitive.db
Competitors tracked: 34 (active: 34)
Today's scans: 31  (strong: 11, weak: 0)
Total scans logged: 578
Total feature-history changes: 60
Positioning features tracked: 24
