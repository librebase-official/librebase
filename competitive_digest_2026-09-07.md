# LibreBase Competitive Intelligence — Daily Scan 2026-09-07

> **Automated daily scan** — Hermes cron at 09:00 CEST weekdays. Scanned 13 known competitors + discovery queries. Confidence scores are coarse heuristics; treat as directional.

## Executive Summary

**42 findings scanned. 18 strong-impact signals. 4 new competitor candidates.** Every major BaaS competitor shipped MCP server support in 2026. The competitive axis has decisively shifted from "who has the best dashboard/SDK" to "who can be driven by an AI coding agent end-to-end."

## Key Signals (Strong Impact)

### Supabase — Evals + MCP maturity
- **Supabase Evals** (Jul 31): Open-source benchmark scoring Claude Code, Codex, and OpenCode on real Supabase tasks. Public results, groupable by agent/product/stage. This is the first BaaS competitor with a published agent-benchmark program — sets a bar LibreBase should match.
- **Supabase MCP Server** (mature): Official remote MCP at `mcp.supabase.com` with OAuth 2.1, 8 tool groups covering full BaaS stack (DB, auth, storage, edge functions, branches, logs, typegen). 2.7K GitHub stars. Read-only mode, scoped project access.
- **Sign in with ChatGPT** (beta, Jul 29): New auth provider — signals Supabase pushing deeper into agentic auth flows.

### Appwrite — Appwrite 2.0 + Remote MCP
- **Appwrite 2.0** (Aug 31): New Hyperloop B engine (7x throughput, 6x less memory vs Swoole), Console IV (rebuilt on TanStack, merges docs/blog/changelog into one app), 5 database types (TablesDB, DocumentsDB, VectorsDB, Native PostgreSQL, Native MySQL), S3-compatible storage API, OAuth 2.1/OpenID Connect provider, Domains + Firewall.
- **Remote MCP Server** (Jul): Hosted at `mcp.appwrite.io`, OAuth auth, no local install/Python dependency. Ships alongside Projects API (programmatic project config), OAuth Device Authorization CLI login.
- **VectorsDB** (Sep 2): Similarity search as first-class database with built-in embedding models — native vector search without separate embedding service.
- **Firewall** (Sep 4): Project-level traffic control — deny/bypass/challenge/rate-limit/redirect with impact preview.
- Pricing: Free tier + Pro $25/mo (same entry as Supabase).

### Nhost — Constellation + MCP
- **Constellation** (Jun 3): Open-source Hasura-compatible GraphQL engine in Go — ~90% less memory than Hasura. Runs alongside Hasura, becoming default over time. Addresses the #1 operational complaint about Hasura-based stacks.
- **MCP Service** (Mar 31): Deploy open-source Nhost MCP service to expose GraphQL API to AI agents with OAuth2 + existing permission model.
- Pricing: Starter free, Pro $25/mo, Team $599/mo. Compute billed separately at $50/vCPU dedicated / $15/vCPU shared.

### Directus — AI Assistant GA + MCP server + V12 on horizon
- **AI Assistant GA** (v11.15, Feb): Multi-provider (OpenAI, Anthropic, Gemini, Ollama-compatible), content-aware (attaches content items/prompts/visual editor elements), now processes images and PDFs (v11.16).
- **Native MCP Server**: Official `directus/mcp` repo — connects Claude, Cursor, ChatGPT directly to data. Same role-based permissions as human users.
- **Collaborative editing** (v11.15): Built into core, WebSocket + Redis, works across multi-instance deployments.
- **Deployment module**: Vercel/Netlify one-click deploys from Data Studio with role-based access + webhook status.
- **V12 upcoming**: Native draft & publishing, redesigned Studio, AI-powered translation tools. New MSCL license — self-hosted free under $5M revenue / 50 employees (OIG grant). Some community concern about telemetry and seat limits on paid tiers.

### Xano — Agent-native no-code backend, most aggressive MCP push
- **Xano Agent** (Apr, v2.3): Build entire backend from natural language — data models, APIs, auth, business logic. Every change inspectable visually (XanoScript synced 1:1 with visual layer).
- **XanoScript GA**: AI-generated backend logic as code that maps directly to visual workflows. Not a translation layer — shared representation.
- **CLI GA + Sandbox** (Apr): Push/pull workspace as XanoScript, work from IDE, integrate with Git. Ephemeral sandbox environments for safe AI change validation.
- **Developer MCP** (Apr): Gives AI coding agents context to build in Xano workspace — reads/writes/validates backend logic through XanoScript, routes every change through sandbox + deployment pipeline.
- **Knowledge** (v2.5, Jul): Workspace-native library of persistent team-authored context (AGENTS.md, Docs, Skills) that Xano Agent + external coding agents read. Admin-lockable, versioned like function stacks, enforced by admins.
- **Error Logs Dashboard** (v2.4): Workspace-wide error visibility across APIs, functions, tasks, triggers, middleware — grouped by signature, states: New/Regression/Ignored/Fixed.
- **Request History Dashboard**: Analytics for success rate, p95 duration, status distribution, HTTP methods, traffic patterns.
- Pricing: Free, Essential $85/mo, Pro $224/mo (annual), Custom enterprise. **Most aggressive MCP integration among no-code platforms.**

### Railway — Agent-first platform pivot
- **Remote MCP Server** (Apr 17): `mcp.railway.com`, OAuth, 7 tools (whoami, list-projects, create-project, list-services, redeploy, accept-deploy, railway-agent). Minimal tool surface + `railway-agent` for multi-step ops.
- **Railway Agent CLI** (`railway agent -p`): Talk to Railway's AI agent from terminal/scripts/CI. Same agent as dashboard.
- **Cloud Agents Beta** (Aug 7): Agent-driven deploy, config, debugging. Postgres Automatic CVE Patching. Railway Mobile App for Android.
- **Access Groups** (Aug 14): Better template editing, agent connectors.
- **ChatGPT plugin** (Jul 31): Railway plugin for ChatGPT.
- **MySQL HA** (Aug 28): High-availability MySQL clusters.
- **Redis HA** (Aug 21): High-availability Redis.
- **Edge Rules** (Aug 21): Edge rules for traffic control.
- Pricing: Hobby $5/mo ($5 credit included), Pro $20/seat/mo ($20 credit included), unlimited seats on Pro. Usage-based billing. **Strongest positioning as "platform for agents" among PaaS competitors.**

### Render — MCP server, OAuth, pricing restructure
- **MCP Server with OAuth** (2026): Hosted at `mcp.render.com`, OAuth (Claude Code, Codex, Cursor, Pi), API key fallback. Expanded from 3 to 20+ skills. Tools: create/manage web services, static sites, cron jobs, databases; query Postgres; inspect logs/metrics; trigger deploys; change service plans.
- **New Workspace Plans** (Apr 23, rolled out Aug 1): Removed seat fees. Scale plan adds SSO, SCIM, advanced RBAC, HIPAA-enabled workspaces, multi-workspace management. Custom domains $0.25/domain/month after included allotment.
- **Postgres connection pooling** (Jul 1): PgBouncer at no additional cost on paid Postgres databases.
- **Postgres + Key Value CLI management** (Jun 30): `render pg` / `render kv` commands for full lifecycle.
- **OIDC for AWS** (2026): Connect Render as identity provider in AWS IAM.
- Pricing concern: April 2026 bandwidth cut — Pro bandwidth dropped from 500 GB to 25 GB, Hobby from 100 GB to 5 GB. Community reaction: "major price hike for indie developers."
- Pricing: Free (limited), Pro $25/mo, Scale $499/mo. Compute from $7/mo (Starter, 512 MB) to $1,500/mo (12 CPU, 96 GB). Postgres from $6/mo (Basic 256MB) to $11,000/mo (96 CPU, 768 GB).

### Fly.io — "Computers for agents" $25M raise + Sprites MCP
- **$25M funding** (Jul 24): "Computers for Agents" — new CEO Scott Johnston. Vision: infrastructure purpose-built for AI agents and the applications they build.
- **Sprites** (Jan 2026, MCP Mar 2026): Stateful Linux sandbox environments for AI agents. Persistent, checkpoint/restore in ~9 seconds, 100 GB ext4 on S3. Sprites expose full lifecycle over MCP at `sprites.dev/mcp` since March 2026 — agents authenticate to org, create machines, exec commands, checkpoint, destroy. "Claude doesn't want a stateless container. Claude wants a computer."
- **Managed Postgres v2 beta** (May 19): Built directly on Fly Machines, Fly networking, Flycast — designed for stability, fewer moving parts. Same pricing as v1. Beta in dfw, expanding.
- **Managed Postgres**: Plans from $38/mo (Basic, 1 GB) to $1,922/mo (Performance, 64 GB). Storage $0.28/GB/month. pgvector + PostGIS extensions. Connection pooling included.
- **GPU support**: A10, L40S, A100 available for AI/ML workloads.
- **35+ global regions**, edge deployment. Scale-to-zero.
- Pricing: Pay-as-you-go, no monthly minimum. Shared CPU VMs from $1.94/mo (256 MB). $0.02/GB bandwidth (NA/EU). No free tier for new orgs since Oct 2024 (short trial only). **Most directly "agent-infrastructure" focused of all competitors.**

### Heroku — Sustaining engineering, but ships MCP server
- **Sustaining Engineering model** (Feb 2026): No new feature roadmap. Security/stability fixes continue. No new Enterprise contracts. **Frozen featureset** — important context for LibreBase positioning vs "innovating alternatives."
- **Official Heroku MCP Server** (2026): Bridges agent-driven development and Heroku AI PaaS. Models: Claude Haiku 4.5, Claude Opus 4.6, Claude Sonnet 4.6, gpt-oss-120b, Kimi K2 Thinking, MiniMax M2.1, Qwen3 235B, Qwen3 Coder 480B — all with MCP tool calling.
- **Heroku AI**: Managed inference and agents. MCP on Heroku for building AI agents that interact with application logic, external APIs, and Heroku services.
- **Fine-Grained Access Control** (Aug 21, 2026): Available to all customers. Replaces legacy role-based system with individual capability controls (deploy, scale, logs, config vars, pipelines, add-ons, members, billing).
- **Pgvector for Heroku Postgres** (May 2026): Vector similarity search in Postgres.
- **Heroku-26 Stack** (Ubuntu 26.04): New stack, Python buildpacks updated.
- **1GB slug limits** (Mar 2026): Doubled from 500 MB.
- **CLI v11**: Rebuilt on ESM + oclif v4. Credentials in system keychain (v11.8.0).
- Pricing: Eco $5/mo (sleeps), Basic $7/mo, Standard-1X $25/mo, Standard-2X $50/mo, Performance-M $250/mo, Performance-L $500/mo. Postgres from $5/mo (Essential-0) to $750/mo (Premium-2). **Sustaining engineering = no innovation threat, but MCP server + agent features are a "stay relevant" signal.**

### AWS Amplify — MCP server + Gen 2
- **AWS MCP Server** (Apr 10, 2026): Pre-built workflows (Agent SOPs) for backend implementation, frontend integration, deployment. Documentation access. AWS API execution from AI assistant. Works with Amazon Kiro, Cursor, Claude Desktop, any MCP-compatible assistant.
- **Gen 2**: TypeScript-based, code-first backend definition. Team workflows with fullstack branching.
- **Unified webhooks** (Mar 2026): Single webhook per region for all Amplify apps in a repo — solves monorepo webhook limits.
- **Node.js 24 support** (May 2026): For SSR applications.
- **Configurable build instance type** (May 2025): Choose CPU/memory/disk for builds.
- **AWS WAF integration GA** (Mar 2025): Firewall for Amplify hosted sites.
- **Skew protection** (Mar 2025): Eliminates version skew between client and server.
- Pricing: No flat plan. $0.01/build minute, $0.15/GB served, $0.023/GB stored, $0.30/1M SSR requests, $0.20/GB-hour SSR duration, $15/month WAF per app. Free tier: 1,000 build minutes, 15 GB bandwidth, 5 GB storage/month (permanent, not 12-month). **Pricing complexity = 이탈 위험 for teams wanting predictability. $0.15/GB egress = 50-100% more expensive than hand-rolled CloudFront+S3 at scale.**

### PocketBase — Vitality concerns + v0.40
- **v0.40.0** (Aug 23, 2026): New UI rewrite, `geoPoint` field + `geoDistance()` function, `strftime()` filter, filesystem hooks (`OnNewWriter`, `OnDelete`), `Store.Keys()`, `Record.GetInt64()`, DELETE /api/logs endpoint, log data size limit, SQLite defensive mode (`_defensive=1`), min Go 1.27.0 + `encoding/json/v2` migration.
- **v0.39.x series**: SQL console under Settings > Debug, email alerts for backup errors, various UI fixes.
- **v0.37.0**: Entire new UI from scratch — ~2 MB smaller bundle, dark mode, basic responsive, ERD-like visualization, API rules overview, stepped logs chart.
- **v0.38.1**: Single-binary realtime backend on SQLite, positioned as self-hostable BaaS alternative to Supabase/Convex.
- **GitHub stars**: ~58K+ (Apr 2026). Active development but still pre-1.0.
- **Roadmap v1.0**: Board exists on GitHub with planned features, no hard deadlines.
- **Vitality concerns**: Reddit threads express concerns about future of PocketBase. FAQ says "no promises for maintenance and support." Project survival questions on GitHub Discussions (#3087 "Will PocketBase survive?").
- **No official MCP server** — community project `mrwyndham/pocketbase-mcp` exists but is behind on PocketBase version and methods don't all work. Third-party MCP guides exist but no official integration.
- **No AI features** — no vector search, no MCP, no agent tooling. Pure SQLite + realtime + auth + dashboard. **Competitive gap vs Supabase/Appwrite/Nhost on agent-native features.**

## New Competitor Candidates (Monitor)

### InsForge (`insforge.dev`)
- AI-native backend for coding agents. Connects to Cursor/Windsurf/Claude Code via MCP. Provisions Postgres + auto-generated APIs + auth + S3 storage + edge functions + compute + AI model gateway from natural language.
- **MCPMark benchmark**: InsForge completes backend tasks in 150s vs Supabase 239s (1.6x), 30% fewer tokens (8.2M vs 11.6M), 1.7x higher accuracy (47.6% vs 28.6%) on 127 tasks.
- Open-source (Apache-2.0). Pricing from $25/mo. Self-hostable.
- **Watch closely** — directly targets the same agent-native wedge LibreBase is pursuing.

### Butterbase (`butterbase.ai`)
- Postgres-backed, MCP-native from ground up. 43 MCP tools. Official Claude Code plugin. "Built so an AI coding agent operates the backend for you over MCP."
- Auth, storage, functions, AI gateway, MCP server. "The most direct fit when the agent — not you — is the one doing the wiring."
- **Direct positioning vs Supabase for agent-driven builders.**

### MoonDB (`moondb.ai`)
- Minimal agent-native backend: JSON schema → hosted database with REST API, auth, file storage in 3 HTTP calls or MCP. SQLite on Cloudflare D1. No vector store, no edge functions, no AI gateway — intentionally narrow.
- "If your generated app needs RAG or serverless compute, InsForge or Butterbase carry more out of the box."
- **Watch** — smallest surface area, may be fastest path for simple agent-built apps.

### Backenly (`github.com/backenly/backenly`)
- Autonomous backend platform: PostgreSQL, REST APIs, auth, storage, realtime, functions. Driven by coding agent over MCP. Every change planned, verified, reversible through `executeAction` kernel — no raw-SQL mutation path. MAPE-K loop monitors and repairs drift, missing indexes, broken triggers, RLS gaps autonomously.
- "Backenly does not just generate backend resources, it manages backend change safely."
- Apache-2.0. **Most sophisticated governance/change-management model among new entrants — closely overlaps LibreBase's "attribution + audit + reversible" design principles.**

## MCP Ecosystem Context

- **MCP joined Linux Foundation's Agentic AI Foundation** (Dec 9, 2025). Co-founders: Anthropic, Block, OpenAI. Platinum: Google, Microsoft, AWS, Cloudflare, Bloomberg.
- **MCP 2026 Roadmap** (Mar 2026): 4 priorities — transport scalability (stateless, horizontal scale, Server Cards), agent communication (Tasks retry/expiry), governance maturation (contributor ladder, working groups), enterprise readiness (audit trails, SSO, gateway patterns).
- **MCP Apps shipped** Jan 26, 2026 — 9 launch partners. Tools return interactive HTML inside Claude, ChatGPT, Goose, VS Code.
- **MCP 2026-07-28 spec**: Streamable HTTP is primary transport (SSE deprecated, 1-year offramp). Stateless — no initialize handshake, no session header. OAuth 2.1 + PKCE. Header-based routing (`Mcp-Method`, `Mcp-Name`). Cache hints (`ttlMs`, `cacheScope`). Mid-call interaction via MRTR `input_required`. 97M+ monthly SDK downloads, 10,000+ active servers.
- **Implication**: Every competitor is moving to remote, OAuth-authenticated, stateless MCP servers. LibreBase's MCP agent API must match this spec to remain competitive.

## Pricing Benchmark Summary

| Competitor | Free Tier | Entry Paid | Key Pricing Trait |
|---|---|---|---|
| Supabase | 500 MB DB, pauses 7d | $25/mo Pro | Per-project compute + 6 meters (DB, egress, cached egress, MAU, storage, compute). MAU $0.00325 over 100K. |
| Appwrite | Yes | $25/mo Pro | Unified subscription, S3-compatible storage, OAuth 2.1, PostgreSQL/MySQL native. |
| Firebase | Spark (limited) | Blaze (usage) | Spark/Blaze. Sep 2026: fetch requests $0.000006 over 100K/day. NoSQL = different cost model. |
| PocketBase | Full (self-host) | Self-host only | Single binary, SQLite. Free forever self-hosted. No managed cloud with comparable pricing. ~58K stars. |
| Nhost | 1 GB DB, pauses 7d | $25/mo Pro | Hybrid flat-rate + usage. Compute $50/vCPU dedicated / $15 shared. $15 credit on Pro. SOC 2 on Team. |
| Directus | OIG free (<$5M rev, <50 emp) | Cloud from ~$25/mo | V12 MSCL license concerns. Self-host free under OIG. Cloud pricing less transparent. |
| Xano | Free | $85/mo Essential | Pro $224/mo annual. Agent-native features included. No-code + CLI + MCP + visual all same platform. |
| Railway | $5 trial credit | $5/mo Hobby | Usage-based, no free tier. Pro $20/seat/mo with $20 credit. Unlimited seats. Autoscaling. |
| Render | Free (sleeps 15min) | $7/mo Starter | Apr 2026: removed seat fees. Bandwidth cut (Pro 500→25 GB). Compute up to $1,500/mo (12 CPU). |
| Fly.io | No (trial only) | ~$2/mo effective | Pay-as-you-go. No monthly minimum. $0.02/GB bandwidth. GPUs. 35+ regions. Sprites for agents. |
| Heroku | No (removed 2022) | $5/mo Eco | Sustaining engineering. Standard-1X $25/mo. Postgres from $5/mo. No new Enterprise contracts. |
| AWS Amplify | Yes (permanent) | Usage-only | $0.01/min build, $0.15/GB serve, $15/mo WAF. No flat plan. Egress 50-100% > CloudFront direct at scale. |
| Koywe | No | Contact | LatAm fiat↔crypto on/off-ramp API. Not a BaaS competitor — payments infrastructure. First agent-signed non-custodial transaction (Codex, Mar 2026). |

## Feature Coverage Matrix

| Feature | LibreBase Target | Supabase | Appwrite 2.0 | Nhost | Directus | Xano | Railway | Render | Fly.io | Heroku |
|---|---|---|---|---|---|---|---|---|---|---|
| PostgreSQL backend | ✓ | ✓ | ✓ (native) | ✓ | ✓ (bring own) | ✓ | ✓ | ✓ | ✓ (MPG) | ✓ |
| MCP server | **WEDGE** | ✓ remote+OAuth | ✓ remote+OAuth | ✓ open-source | ✓ official | ✓ + XanoScript | ✓ remote+OAuth | ✓ remote+OAuth | ✓ Sprites MCP | ✓ official |
| Agent benchmark | — | ✓ Evals (public) | — | — | — | — | — | — | — | — |
| Vector/search | — | pgvector | VectorsDB+bundled embeddings | pgvector+Graphite AI | — | — | — | — | pgvector (MPG) | pgvector |
| Auth/OAuth2 | — | ✓ | ✓ OAuth 2.1/OIDC | ✓ OAuth2/OIDC | ✓ | ✓ | — | — | — | ✓ Cognito |
| Storage S3-compatible | — | ✓ | ✓ S3 API | — | — | — | — | — | — | S3-backed |
| Edge functions | — | ✓ Deno | ✓ (Bun/Deno/Rust/Dart) | ✓ Node.js/TS | — | ✓ | — | — | — | ✓ Lambda-backed |
| Postgres v2 rebuild | — | — | ✓ Hyperloop B | ✓ Constellation (Go) | — | — | — | — | ✓ MPG v2 (Fly Machines) | — |
| Governance/audit | **WEDGE** | — | — | — | — | ✓ Knowledge (versioned, admin-locked) | — | — | — | FGAC (Aug 2026) |
| Pricing predictability | **WEDGE** | Complex (6 meters) | Unified subscription | Hybrid flat+usage | OIG free / cloud varies | Tiered | Usage-based, cap | Flat+usage, bandwidth cut | Pay-as-you-go, no minimum | Dyno-tiered, opaque at scale |

## Coverage Gaps (sources that returned no data or JS-rendered pages)

- **None this scan.** All 13 competitors returned usable search results. Discovery queries surfaced 4 new competitors with public docs/sites.

## Strategic Read

1. **MCP is now table stakes.** Every competitor from Supabase to Heroku to Fly.io has shipped an official remote MCP server with OAuth. LibreBase's MCP agent API is the right wedge, but the window for "first mover among self-hosted/open BaaS" is narrowing. Appwrite, Nhost, Directus, Xano, Railway, Render, Fly.io, Heroku, and AWS Amplify all have MCP servers live. Supabase has the benchmark program (Evals) that no one else matches.

2. **Agent-native backends are the emerging category.** InsForge, Butterbase, MoonDB, and Backenly are not traditional BaaS — they're built from the ground up to be operated by AI coding agents via MCP/HTTP. InsForge's MCPMark numbers (1.6x faster, 30% fewer tokens, 1.7x accuracy vs Supabase) are early but directionally significant. Backenly's governed change kernel (no raw-SQL mutation, MAPE-K repair loop) directly overlaps LibreBase's auditability/reversibility design principles.

3. **Pricing predictability is a real wedge.** Supabase's 6-meter billing, Render's bandwidth cut, AWS Amplify's egress premium, and Railway's usage surprises are all pain points. A BaaS that offers predictable flat pricing + self-host escape hatch aligns with the "publisher/artist/independent" audience LibreBase targets.

4. **Sustaining-engineering competitors are vulnerable.** Heroku froze its roadmap. PocketBase has vitality concerns and no official MCP/AI story. These are repositioning opportunities, not innovation threats.

---

## DB Status
DB: /Users/julian/Documents/coding-projects/librebase/librebase_competitive.db
Competitors tracked: 34 (active: 34)
Today's scans: 42  (strong: 18, weak: 0, new_competitor: 4, noise: 11, feature_changes: 1)
Total scans logged: 208
Total feature-history changes: 51
Positioning features tracked: 24

*Digest generated 2026-09-07 by Hermes cron (librebasemarketresearch profile). Scan CLI: librebase_competitive_scan.py.*
