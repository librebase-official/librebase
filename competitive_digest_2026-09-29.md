# LibreBase Competitive Intelligence — Daily Scan 2026-09-29

> **Automated daily scan** — Hermes cron at 09:00 CEST weekdays. Scanned 13 known competitors + 6 discovery queries. Confidence scores are coarse heuristics; treat as directional.

DB: /Users/julian/Documents/coding-projects/librebase/librebase_competitive.db
Competitors tracked: 34 (active: 34)
Today's scans: 44  (strong: 22, weak: 0)
Total scans logged: 547
Total feature-history changes: 59
Positioning features tracked: 24

## 🚨 STRONG SIGNAL ALERTS

### Supabase — Enterprise-managed auth for the Supabase MCP server — Okta integration
- **Feature:** mcp-agent-api
- **Impact:** 🔴 strong
- **Confidence:** 85%
- **Source:** https://supabase.com/blog
- **Delta:** Supabase now lets enterprise IT admins manage MCP server access via Okta. Directly competitive with LibreBase's MCP auth story.

### Supabase — Supabase MCP Server v0.8.x: 8 tool groups, OAuth 2.1, hosted at mcp.supabase.com
- **Feature:** mcp-agent-api
- **Impact:** 🔴 strong
- **Confidence:** 90%
- **Source:** https://mcp.directory/blog/supabase-mcp-complete-guide-2026
- **Delta:** Most complete BaaS MCP implementation — 8 tool groups, OAuth 2.1, read-only mode, BYO MCP on Edge Functions. Sets the standard LibreBase should benchmark against.

### Supabase — Supabase Evals: open-source Apache-2.0 benchmark for AI coding agents
- **Feature:** mcp-agent-api
- **Impact:** 🔴 strong
- **Confidence:** 88%
- **Source:** https://www.marktechpost.com/2026/08/01/supabase-releases-evals-an-open-source-benchmark-that-scores-claude-code-codex-and-opencode-on-real-supabase-tasks/
- **Delta:** Supabase open-sourced evals (Aug 1, 2026) — reproducible benchmark harness running agents against containerized Supabase stacks. Public leaderboard at supabase.com/evals. They're defining how agents are evaluated on BaaS platforms. LibreBase needs its own eval harness.

### Supabase — Sign in with ChatGPT beta + Studio AI assistant + ISO 27001
- **Feature:** mcp-agent-api
- **Impact:** 🔴 strong
- **Confidence:** 78%
- **Source:** https://supabase.com/blog/sign-in-with-chatgpt-beta
- **Delta:** OpenAI launch partner, Studio "Fix with Assistant" buttons, ISO 27001:2022 certified (April 2026), SOC 2 + HIPAA.

### Appwrite — Appwrite MCP server now remote + Projects API + Console IV + Claude marketplace
- **Feature:** mcp-agent-api
- **Impact:** 🔴 strong
- **Confidence:** 85%
- **Source:** https://appwrite.io/blog/post/july-product-update-remote-mcp-server-projects-api-and-more
- **Delta:** Hosted remote MCP server at mcp.appwrite.io with OAuth (July 2026). Console IV rebuilt on TanStack Start. Plugin in official Claude marketplace.

### Appwrite — Appwrite MCP server: hosted remote with OAuth 2.0
- **Feature:** mcp-agent-api
- **Impact:** 🔴 strong
- **Confidence:** 82%
- **Source:** https://claudewave.com/en/repo/appwrite-mcp
- **Delta:** MIT licensed, 71 stars. Works with Claude Code, Cursor, Codex, VS Code, Windsurf, Zed. Context-efficient architecture.

### Firebase — Firebase MCP server GA + Agent Skills + eval-driven development
- **Feature:** mcp-agent-api
- **Impact:** 🔴 strong
- **Confidence:** 82%
- **Source:** https://firebase.google.com/docs/ai-assistance/mcp-server
- **Delta:** Firebase MCP server GA. Agent Skills with eval-driven development. Firebase Studio sunsetting March 2027 → Antigravity.

### Firebase — Eval-driven development for agent skills + multimodal AI Assistant
- **Feature:** mcp-agent-api
- **Impact:** 🔴 strong
- **Confidence:** 78%
- **Source:** https://firebase.blog/posts/2026/08/eval-driven-development-agent-skills
- **Delta:** Published eval-driven development process. AI Assistant now multimodal (images, PDFs).

### Directus — Directus v12: native draft/publishing, AI translations, OAuth 2.1 for MCP, JSON filtering
- **Feature:** mcp-agent-api
- **Impact:** 🔴 strong
- **Confidence:** 85%
- **Source:** https://directus.io/resources/v12-built-for-the-whole-team
- **Delta:** v12 ships native draft & publishing, AI-assisted translations, JSON dot-notation filtering, OAuth 2.1 for MCP. Major AI-agent-ready release from a headless CMS player.

### Directus — Directus native MCP server with OAuth 2.1 + multimodal AI Assistant
- **Feature:** mcp-agent-api
- **Impact:** 🔴 strong
- **Confidence:** 85%
- **Source:** https://directus.com/docs/guides/ai/mcp/oauth
- **Delta:** Native MCP since Sept 2025, OAuth 2.1 in v12. AI Assistant processes images and PDFs. Included on every tier including free.

### Directus — Directus AI: governed data for AI — MCP server, AI Assistant, AI Translations
- **Feature:** vector-embeddings
- **Impact:** 🔴 strong
- **Confidence:** 82%
- **Source:** https://directus.com/ai
- **Delta:** "The backend where AI works under your rules." Every action logged, data stays in your DB. SOC 2 Type II, GDPR. Selling same AI-native backend story as LibreBase.

### Nhost — Nhost AI Week: Postgres Vector + Auto-Embeddings + Assistants + Dev Assistant + Graphite
- **Feature:** vector-embeddings
- **Impact:** 🔴 strong
- **Confidence:** 82%
- **Source:** https://nhost.io/blog/ai-week-release-day
- **Delta:** Postgres as vector DB with pgvector + Auto-Embeddings. Nhost Assistants, Dev Assistant in dashboard, Graphite AI on Pro plan. Auth now OAuth2/OIDC provider.

### Xano — Xano Q2 2026: Xano Agent, CLI GA, XanoScript GA, Developer MCP, Sandbox, Knowledge for Agents
- **Feature:** mcp-agent-api
- **Impact:** 🔴 strong
- **Confidence:** 88%
- **Source:** https://community.xano.com/product-updates/post/state-of-xano-q2-2026-h2PLnzEttXFee4O
- **Delta:** Most aggressive AI-native BaaS strategy alongside Supabase. Xano Agent (workspace-wide), CLI GA, XanoScript GA, Developer MCP, Sandbox, Knowledge for Agents (v2.5, RBAC-governed AGENTS.md/Docs/Skills).

### Xano — Xano Developer MCP + native MCP server + OAuth proxy + Claude marketplace
- **Feature:** mcp-agent-api
- **Impact:** 🔴 strong
- **Confidence:** 85%
- **Source:** https://docs.xano.com/updates
- **Delta:** Native MCP server, Developer MCP for local IDE, OAuth proxy (Cloudflare Worker) for Claude connectors. BYOC AI. Knowledge library syncs to external agents.

### Railway — Railway Remote MCP server + Railway Agent CLI + one-command skills install
- **Feature:** mcp-agent-api
- **Impact:** 🔴 strong
- **Confidence:** 82%
- **Source:** https://railway-com.translate.goog/changelog/2026-04-17-remote-mcp
- **Delta:** Remote MCP at mcp.railway.com (April 2026), 7 tools, OAuth. railway agent CLI. One-command skills install for Claude Code, Cursor, Codex, OpenCode. Also runs bex (open-source Render alternative) with 13 MCP tools.

### Render — Render MCP server with trigger_deploy + Workflows beta + 12-CPU plans for agents + OIDC
- **Feature:** mcp-agent-api
- **Impact:** 🔴 strong
- **Confidence:** 82%
- **Source:** https://render.com/changelog/render-workflows-now-in-public-beta
- **Delta:** MCP server GA with 20+ tools, trigger_deploy added. Workflows public beta (durable tasks for agent logic). New 12-CPU compute plans specifically for "agent platforms." Managed OIDC for Anthropic/OpenAI.

### Fly.io — Fly.io $25M Series D + Sprites MCP server + "Computers for Agents" strategy
- **Feature:** mcp-agent-api
- **Impact:** 🔴 strong
- **Confidence:** 85%
- **Source:** https://fly.io/news/fly-io-launches-computers-for-agents/
- **Delta:** $25M Series D (July 24, 2026) co-led by Dell + Intel Capital. Vision: "Computers for Agents." Sprites MCP server. Claude Code, Gemini, Codex preinstalled on every Sprite. New CEO Scott Johnston.

### Fly.io — Fly.io Sprites MCP server + flyctl MCP server — agents provision/manage/execute in isolated Sprites
- **Feature:** mcp-agent-api
- **Impact:** 🔴 strong
- **Confidence:** 88%
- **Source:** https://fly.io/blog/sprites-mcp/
- **Delta:** Two MCP surfaces: Sprites MCP (hosted, for isolated Linux computers) + flyctl MCP (provision apps, machines, orgs, certs, logs, secrets, volumes). Safety annotations: read-only vs destructive. "Your Agent Speaks MCP. Give It a Computer."

### Heroku — Heroku MCP Server (STDIO + Remote) + Managed Inference and Agents + Fir platform
- **Feature:** mcp-agent-api
- **Impact:** 🔴 strong
- **Confidence:** 80%
- **Source:** https://devcenter.heroku.com/articles/heroku-remote-mcp-server
- **Delta:** Both STDIO and Remote MCP (OAuth 2.0). Managed Inference and Agents add-on with MCP toolkits. Fir platform (Kubernetes, OpenTelemetry, GPU dynos coming). Fine-Grained Access Control GA. Sustaining Engineering model = slower velocity.

### Heroku — Heroku MCP Server: 16+ tools for app lifecycle, Postgres, add-ons, pipelines
- **Feature:** mcp-agent-api
- **Impact:** 🔴 strong
- **Confidence:** 80%
- **Source:** https://devcenter.heroku.com/articles/heroku-mcp-server
- **Delta:** 16+ tools: app lifecycle, Postgres management (pg_psql, pg_info, pg_locks, pg_outliers, pg_upgrade), add-ons, pipelines. Remote MCP at mcp.heroku.com with OAuth 2.0.

### AWS Amplify — AWS MCP Server GA + Amplify MCP Server (remote) + Agent SOPs
- **Feature:** mcp-agent-api
- **Impact:** 🔴 strong
- **Confidence:** 80%
- **Source:** https://aws.amazon.com/about-aws/whats-new/2026/05/aws-mcp-server/
- **Delta:** AWS MCP Server GA (May 6, 2026). IAM guardrails, CloudWatch, CloudTrail. Sandboxed Python execution. Amplify-specific MCP server RFC: remote at amplify-mcp.global.api.aws with backend/frontend/deployment guidance.

### AWS Amplify — AWS Amplify MCP Server: remote at amplify-mcp.global.api.aws
- **Feature:** mcp-agent-api
- **Impact:** 🔴 strong
- **Confidence:** 75%
- **Source:** https://github.com/awslabs/mcp/issues/1644
- **Delta:** RFC closed Jan 2026. Addresses problem that AI generates working Amplify apps only 10% of time. Multi-framework: React, Vue, Angular, Next.js, React Native, Flutter, Swift, Android.

---

## ⚪ Other (noise / new-competitor / neutral — logged for record)

- **Appwrite** — Appwrite pricing update: Pro $25/mo (was $15), per-project model, +500% bandwidth *(⚪ Comparable)*
- **Firebase** — Firebase pricing: Spark free + Blaze pay-as-you-go. Remote Config new pricing Sept 1, 2026 *(⚪ Comparable)*
- **Directus** — Directus pricing 2026: free self-hosted, Cloud Starter $15, Standard $99, Professional $299 *(⚪ Comparable)*
- **PocketBase** — v0.40.2 (Sep 2, 2026): rapid weekly releases, UI rewrite, 60k+ stars *(· noise)*
- **PocketBase** — v0.38.0-v0.40.2: UI rewrite, cross-process sync, security headers *(· noise)*
- **Nhost** — Constellation: open-source Hasura-compatible GraphQL engine in Go *(· noise)*
- **Nhost** — Nhost pricing: Starter free, Pro $25/mo, Team $599/mo, Graphite AI add-on *(⚪ Comparable)*
- **Xano** — Xano pricing: Free, Pro $224/mo, HIPAA $500/mo add-on *(⚪ Comparable)*
- **Railway** — Railway pricing: Hobby $5/mo flat, usage-based. No managed DBs *(⚪ Comparable)*
- **Render** — Render pricing 2026: Hobby free, Pro $25/mo flat (not per-seat), Scale $499/mo *(⚪ Comparable)*
- **Render** — Render Postgres: PgBouncer connection pooling, new compute plans, OIDC *(⚪ Comparable)*
- **Fly.io** — Fly.io Managed Postgres + Sprites RAM/storage + egress IPs + Machines API *(⚪ Comparable)*
- **Fly.io** — Fly.io pricing: usage-based, shared CPU from ~$1.94/mo, Reservation Blocks 40% discount *(⚪ Comparable)*
- **Heroku** — Heroku pricing 2026: Eco $5, Basic $7, Standard-1X $25, Performance-M $250. Fir dynos usage-based *(⚪ Comparable)*
- **AWS Amplify** — AWS Amplify: pay-as-you-go, no flat BaaS tier *(⚪ Comparable)*
- **Koywe** — Koywe: limited 2026 data — needs further investigation *(· noise)*

### 🆕 New competitors discovered (6)

- **InsForge** — YC Spring 2026, $1.5M pre-seed, agent-native open-source BaaS (Apache-2.0) with MCP + CLI + Skills. Postgres + PostgREST, Deno edge functions, S3 storage, LLM gateway. "Dashboard is an afterthought. Primary user is a coding agent." GitHub stars 2K-10K+. **Most directly competitive new entrant to LibreBase.**
- **Butterbase** — Open-source BaaS with built-in MCP server, Postgres, auth, storage, Deno functions, AI gateway, 30+ Claude skills. Self-host Docker. Durable per-key actors. Three Postgres planes.
- **Open Source Cloud (OSaaS)** — Deploy 188 unmodified open-source services via MCP. Zero vendor lock-in. Entry tier 15 EUR/mo. Different model — OSS deployment platform, not BaaS.
- **Powabase** — AI-native BaaS built on Supabase components (Postgres, auth, storage, PostgREST) + prebuilt agentic layer: knowledge bases with embedding pipelines, agents, workflows. Self-host Docker/Helm + managed cloud + OSS community edition.
- **InsForge + Butterbase + Powabase** — Three new agent-native BaaS platforms built on Postgres, all with MCP. Confirms MCP is table stakes; differentiator is agent-first design.
- **InsForge + Butterbase + Powabase (self-host)** — All three self-hostable. InsForge most open (Apache-2.0). Powabase adds RAG + agents + workflows. Butterbase adds durable actors + AI gateway. Directly competes with LibreBase's self-host positioning.

---

## 🔎 Queries run today (44 total)

AWS Amplify (3), Appwrite (3), Directus (4), Firebase (3), Fly.io (3), Heroku (3), Koywe (1), Nhost (3), PocketBase (2), Railway (2), Render (3), Supabase (4), Xano (3), discovery (6).

---

## 📊 Strategic Takeaways

1. **MCP is now table stakes.** Every serious BaaS/paas platform shipped an MCP server in 2026. The question is no longer "does it work with agents" but "what happens when the agent is wrong." LibreBase's MCP server is necessary but not differentiators.

2. **Supabase is the benchmark.** Their MCP server (8 tool groups, OAuth 2.1, read-only mode, project scoping, BYO MCP) + Evals benchmark (Apache-2.0, public leaderboard) + Sign in with ChatGPT + ISO 27001 is the most complete AI-native BaaS story. LibreBase should benchmark against this holistically.

3. **Three new agent-native BaaS platforms emerged.** InsForge (YC-backed, Apache-2.0, most open), Butterbase (30+ skills, durable actors), Powabase (RAG + agents + workflows on Supabase components). All self-hostable. All designed for AI agents first. This is LibreBase's direct competitive zone.

4. **Xano is the most aggressive AI-native strategy.** Knowledge for Agents (RBAC-governed AGENTS.md/Docs/Skills), Developer MCP, XanoScript, Sandbox, Xano Agent — they're building the governance layer for AI-generated backends. LibreBase should watch their Knowledge feature closely.

5. **Directus is an unexpected threat.** A headless CMS with native MCP (OAuth 2.1), multimodal AI Assistant, AI Translations, governed data for AI — selling the same "AI works under your rules" story. Included on every tier including free. SOC 2 Type II.

6. **Fly.io is betting big on agent infrastructure.** $25M Series D, "Computers for Agents" vision, Sprites MCP server with preinstalled agents. This is infrastructure-layer competition, not BaaS — but agents need somewhere to run.

7. **Pricing parity emerging.** Supabase Pro $25, Appwrite Pro $25, Nhost Pro $25, Render Pro $25 — the $25/mo flat tier is the standard. LibreBase's starter/pro pricing should align here.

---

*Generated by LibreBase Competitive Intelligence Scanner. DB: librebase_competitive.db*
