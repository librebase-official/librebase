# LibreBase Competitive Intelligence — Daily Scan 2026-08-29

> **Automated daily scan** — Hermes cron at 09:00 CEST weekdays. Scanned 13 known competitors + 6 discovery queries. Confidence scores are coarse heuristics; treat as directional.

---

## 📈 Feature Changes (today)

- **Appwrite** — `mcp-agent-api` none → yes ⬆️
- **Firebase** — `mcp-agent-api` none → yes ⬆️
- **Firebase** — `postgresql-db` none → yes ⬆️
- **PocketBase** — `mcp-agent-api` none → yes ⬆️
- **Nhost** — `vector-embeddings` none → yes ⬆️
- **Directus** — `mcp-agent-api` none → yes ⬆️
- **Directus** — `vector-embeddings` none → yes ⬆️
- **Railway** — `mcp-agent-api` none → yes ⬆️
- **Render** — `mcp-agent-api` none → yes ⬆️
- **Fly.io** — `mcp-agent-api` none → yes ⬆️
- **Heroku** — `mcp-agent-api` none → yes ⬆️
- **AWS Amplify** — `mcp-agent-api` none → yes ⬆️

## 🔴 Where LibreBase Is WEAK (12 attack surfaces today)

### mcp-agent-api — 11 competitors now have it

Every major competitor now ships an MCP server or agent plugin. This is the single most important competitive signal today.

| Competitor | What they shipped | Confidence |
|---|---|---|
| **Supabase** | MCP server with 20+ tools (SQL, schema, migrations, Edge Functions, logs, branches); also open-sourced Evals benchmark for Claude Code/Codex/OpenCode | 85% |
| **Appwrite** | Cursor plugin (10 skills + 2 MCP servers + 2 CLI commands); MCP Server 2.0 hosted at mcp.appwrite.io with OAuth | 80% |
| **Firebase** | Integrated with Google Antigravity 2.0 (one-click setup, Agent Skills + MCP); official MCP server for Antigravity/Cursor/Claude Code; Agent Skills expanded to mobile | 85% |
| **PocketBase** | Community MCP servers emerging (third-party) | 60% |
| **Directus** | Native MCP server — Claude, ChatGPT, Cursor manage content directly; AI agents under same RBAC as humans | 85% |
| **Railway** | Remote MCP at mcp.railway.com + CLI proxy + `railway agent` command; supports Claude, Cursor, Codex, Copilot, OpenCode | 80% |
| **Render** | MCP with OAuth, 20+ skills, deploy triggers, service plan changes, full CLI lifecycle | 80% |
| **Fly.io** | MCP server inside flyctl — create/destroy apps, scale machines, inspect volumes, set secrets; $25M raised for "computers for agents" | 75% |
| **Heroku** | MCP on Heroku — register custom MCP servers, Managed Inference and Agents add-on, MCP servers marketplace | 75% |
| **AWS Amplify** | AWS Agent Toolkit GA — managed MCP exposing 15,000+ API actions, 43 Agent Skills; 8-agent-product launch at NYC Summit | 85% |
| **Nhost** | Postgres Vector + Auto-Embeddings + Dev Assistant + Graphite AI product | 75% |

### postgresql-db — Firebase SQL Connect

- **Firebase** evolved Data Connect into **SQL Connect** at Cloud Next 2026: realtime sync, offline cache, native SQL over Cloud SQL for PostgreSQL — no-cost trial.

## 🔎 New Competitor Candidates (3 discovered)

1. **backenly** — Autonomous backend platform driven by coding agent over MCP; governed change kernel, Postgres/REST/auth/storage/realtime/functions. [github.com/backenly/backenly](https://github.com/backenly/backenly)
2. **Knack MCP Server** — HIPAA-compliant relational backend connecting Claude, Lovable, ChatGPT, Bolt to secure data layer; BAA available. [PR Newswire, Aug 26 2026](https://www.prnewswire.com/news-releases/knack-launches-mcp-server-the-hipaa-compliant-backend-for-ai-builders-302860109.html)
3. **Harper 5.1** — MCP-native application platform; auto-generates secure MCP tools from app schema; RBAC at tool level; audit trail. [harper.fast](https://www.harper.fast/resources/your-applications-mcp-native)

## ⚪ Other (noise / neutral — logged for record)

- Supabase pricing restructured: compute by hours, free tier pauses after 7 days, Team $599/mo
- Appwrite Realtime billing enforced April 30, 2026
- Nhost Constellation: Hasura-compatible GraphQL in Go, ~90% less memory
- Directus moved to MSCL license (v12), retired Starter Cloud tier
- Railway Railpack + Functions primitive + Central Station community hub
- Render: AI-agent-specific features (preview envs as agent sandboxes, render pg create CLI, three-tier memory architecture)
- Fly.io: $25M funding for agent infrastructure, MPGv2 expanding to more regions
- Heroku: sustaining engineering model (Feb 2026), CLI v11 ESM migration, 1GB slug limits
- Koywe: fintech payment API for LatAm — NOT a BaaS competitor

---

## DB Status

- **DB:** `/Users/julian/Documents/coding-projects/librebase/librebase_competitive.db`
- **Competitors tracked:** 13 (active: 13)
- **Today's scans:** 36 (strong: 20, weak: 0)
- **Total scans logged:** 36
- **Total feature-history changes:** 12
- **Positioning features tracked:** 24
