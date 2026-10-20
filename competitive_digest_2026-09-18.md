# LibreBase Competitive Intelligence — Daily Scan 2026-09-18

> **Automated daily scan** — Hermes cron at 09:00 CEST weekdays. Scanned 13 known competitors + discovery queries. Confidence scores are coarse heuristics; treat as directional.

**Scanned 28 findings today across 12 known competitors.**

## 🚨 STRONG SIGNAL ALERTS

_These findings indicate a competitor is strong on a feature where LibreBase is weak or neutral. Action recommended._

### Supabase — MCP Server, Evals, Enterprise Auth

- **Supabase MCP Server** — Remote hosted at `mcp.supabase.com` with 20+ tools. Enterprise Okta SSO added Aug 24. **Direct competitor to LibreBase MCP-agent-api.**
- **Supabase Evals** — Open-source benchmark (Jul 31) scoring Claude Code (53.2%), Codex, OpenCode on real Supabase tasks. Public leaderboard at `supabase.com/evals`. **Strong agent-eval positioning.**
- **Enterprise-managed auth for MCP server** — Okta integration, scoped to existing permissions. Aug 24.

### Xano — Xano Agent, XanoScript GA, Developer MCP

- **Xano Q2 2026** ships Xano Agent (replaces Logic Assistant), XanoScript GA, CLI GA, Sandbox environments, Developer MCP with live XanoScript validation. **Strong 'backend for AI-generated code' positioning.**
- Developer MCP connects Claude Code, Cursor, Copilot, Codex. Knowledge feature gives agents team-specific build context. Sandbox + dry-run preview for safe agent deployments.

### Fly.io — Sprites, $25M Series D, Sprites MCP

- **Fly.io raises $25M** (Dell, Intel, a16z). 'Computers for agents' positioning. Sprites: hardware-isolated persistent Linux computers with Claude Code, Gemini, Codex preinstalled.
- **Sprites MCP server** at `sprites.dev/mcp`. Agents can create/control Sprites, run commands, checkpoint, manage services. Plugins for 8+ coding agents. **Highest-confidence MCP finding today (90%).**

### Firebase — MCP GA, 30+ Tools, Firestore Remote MCP

- Firebase MCP server GA since Oct 2025, ships inside `firebase-tools` (1.6M+ weekly npm downloads). Firestore Remote MCP GA Apr 23. 30+ tools across 10+ service categories. CLI Agent Mode + AI Logic with Gemini.

### Appwrite 2.0 — PostgreSQL + MySQL, S3 API, OAuth 2.1

- Appwrite 2.0 ships native PostgreSQL + MySQL support, S3-compatible storage, OAuth 2.1 server. MCP server now remote at `mcp.appwrite.io`. Major expansion from NoSQL-only.

### Directus v12 — MSCL License, Native MCP, AI Assistant GA

- Directus v12: MSCL license (replacing BSL), AI-assisted translations, multimodal AI, OAuth 2.1 for MCP. Built-in MCP server (v11.12+) with 20+ tools, OAuth for Claude Code/Cursor/Codex/ChatGPT.

### Nhost — Constellation GraphQL (Go), MCP Service

- Constellation: open-source Hasura-compatible GraphQL engine in Go. Nhost MCP service: open-source Go service exposing GraphQL via MCP with per-user OAuth2 auth. Respects existing RLS permissions.

### Railway & Render — Remote MCP Servers

- **Railway** remote MCP at `mcp.railway.com` (Apr 17), 7 tools, one-command skills install.
- **Render** MCP with OAuth for Claude Code/Codex/Cursor, expanded from 3 to 20+ skills, trigger_deploy tool.

### AWS Amplify — DevOps Agent, MCP/A2A Protocols

- AWS DevOps Agent adds custom SRE agents, MCP/A2A protocols (Jun 15). Amplify Gen 2 agent plugins for Claude Code + Cursor with 4-phase workflow.

## 🆕 New Competitors Discovered (5)

| Competitor | Description | URLs |
|---|---|---|
| **InsForge** | Open-source BaaS for AI agents, YC-backed, MCP-first. Alpha Mar 2026, v2.3.1 Aug 12. | [Article](https://dev.to/danieltechlab/insforge-rebuilt-the-baas-stack-so-ai-agents-not-humans-are-the-primary-operator-34im) |
| **Rayfin** | Open-source BaaS on Microsoft Fabric, MIT-licensed, 590 stars. TypeScript decorators, Entra ID auth. | [Article](https://wenfeng.my/microsoft-fabric-apps-rayfin-open-source-baas) |
| **Neon** | Postgres backends for apps and agents, GA. Lakebase Postgres, Functions, AI Gateway. Part of Databricks. | [neon.com](https://neon.com/) |
| **Nile** | Postgres platform with tenant virtualization, serverless+provisioned compute. AI-native B2B. Public preview. | [Blog](https://www.thenile.dev/blog/nile-public-launch) |
| **PlanetScale Neki** | Sharded Postgres, platform preview Sep 10. Router speaks Postgres wire protocol, real Postgres on every shard. | [Blog](https://planetscale.com/blog/introducing-neki) |

## 🟢 LibreBase Strengths (competitor weak)

- **PocketBase** — No official MCP server. Community options only (tokenscompany, feirelles). Weak agent support = opportunity for LibreBase.
- **Heroku** — Sustaining engineering model (Feb 6). Platform momentum declining. Fir platform generation still in progress.

## 📊 DB Summary

- **Competitors tracked:** 34 (all active)
- **Today's scans:** 28 (strong: 18, weak: 2, new-competitor: 5, neutral: 3)
- **Total scans logged:** 366
- **Feature-history changes:** 57 (1 today — Heroku postgresql-db went from 'yes' to 'none')
- **Positioning features tracked:** 24

## 🔴 MCP-Agent-API: The Dominant Theme

**14 of 18 strong signals are on `mcp-agent-api`.** Every major competitor now has an MCP story:

| Competitor | MCP Status | Confidence |
|---|---|---|
| Supabase | Remote MCP + Evals + Okta SSO | 90% |
| Fly.io | Sprites MCP + 8 plugins | 90% |
| Xano | Developer MCP + XanoScript validation | 90% |
| Appwrite | Remote MCP + Projects API | 85% |
| Firebase | MCP GA, 30+ tools, 1.6M npm downloads | 85% |
| Directus | Built-in MCP, 20+ tools, OAuth | 85% |
| Nhost | MCP service + OAuth2 per-user auth | 85% |
| Railway | Remote MCP, 7 tools | 80% |
| Render | MCP OAuth, 20+ skills | 80% |
| AWS Amplify | MCP/A2A protocols, agent plugins | 80% |

**MCP-agent-api is the most contested surface in the backend platform market right now.** LibreBase's positioning here is weak relative to this breadth of competition. The window for differentiation is narrowing as MCP becomes table stakes.

## Raw scan data

- **Scan JSON:** `/tmp/scan_findings.json`
- **Digest file:** `/Users/julian/Documents/coding-projects/librebase/competitive_digest_2026-09-18.md`

---

_This digest was generated by LibreBase's automated competitive intelligence pipeline. Findings are based on web search results and should be verified before use in strategic decisions._
