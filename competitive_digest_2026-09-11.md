# LibreBase Competitive Intelligence — Daily Scan 2026-09-11

> **Automated daily scan** — Hermes cron at 09:00 CEST weekdays. Scanned 13 known competitors + discovery queries. Confidence scores are coarse heuristics; treat as directional.

Scanned 33 findings today across 13 known competitors.

## 🚨 STRONG SIGNAL ALERTS

_These findings indicate a competitor is strong on a feature where LibreBase is weak or neutral. Action recommended._

### Supabase — Supabase Series F — Multigres v0.1 alpha, scalable Postgres OS

- **Feature:** `postgresql-db`
- **Impact:** 🔴 strong (competitor gaining on LibreBase)
- **Confidence:** 70%
- **Source:** https://supabase.com/blog/series-f
- **LibreBase delta:** Watch: Supabase raising Series F and shipping Multigres v0.1 alpha — a self-hostable scalable OS for Postgres with Vitess-grade horizontal scaling planned. Signals deepening Postgres investment.

### Supabase — Supabase MCP Server — official MCP server for AI agents

- **Feature:** `mcp-agent-api`
- **Impact:** 🔴 strong (competitor gaining on LibreBase)
- **Confidence:** 85%
- **Source:** https://supabase.com/docs/guides/ai-tools/mcp
- **LibreBase delta:** Direct competitive signal: Supabase ships an official MCP server (mcp.supabase.com) giving AI agents structured access to projects. LibreBase must ship its own MCP server to stay competitive.

### Supabase — Supabase Assistant v2 — AI assistant in Dashboard with schema design, SQL, RLS, functions, triggers

- **Feature:** `mcp-agent-api`
- **Impact:** 🔴 strong (competitor gaining on LibreBase)
- **Confidence:** 80%
- **Source:** https://supabase.com/blog/supabase-ai-assistant-v2
- **LibreBase delta:** Watch: Supabase Assistant v2 expands AI into schema design, RLS policies, Postgres functions/triggers, SQL-to-client conversion. AI is becoming a first-class Supabase DX surface.

### Appwrite — February and March product update: Realtime queries, Appwrite Skills, new database features

- **Feature:** `mcp-agent-api`
- **Impact:** 🔴 strong (competitor gaining on LibreBase)
- **Confidence:** 75%
- **Source:** https://appwrite.io/blog/post/february-and-march-product-update-realtime-queries-appwrite-skills-and-new-database-features
- **LibreBase delta:** Watch: Appwrite shipping relationship queries, new text column types (varchar/text/mediumtext/longtext), Realtime channel helpers, and Appwrite Skills — explicit AI-coding-era tooling.

### Appwrite — July product update: Remote MCP server, Projects API, OAuth Device Authorization

- **Feature:** `mcp-agent-api`
- **Impact:** 🔴 strong (competitor gaining on LibreBase)
- **Confidence:** 85%
- **Source:** https://appwrite.io/blog/post/july-product-update-remote-mcp-server-projects-api-and-more
- **LibreBase delta:** Direct competitive signal: Appwrite's MCP server is now a hosted remote server (mcp.appwrite.io) with OAuth — no local install required. AI tools get structured access to Appwrite projects + documentation. This is the gold standard for BaaS MCP UX.

### Firebase — August 2026: AI Logic, CLI Agent Mode, and App Check — top 6 Firebase updates

- **Feature:** `mcp-agent-api`
- **Impact:** 🔴 strong (competitor gaining on LibreBase)
- **Confidence:** 70%
- **Source:** https://firebase.google.com/
- **LibreBase delta:** Watch: Firebase shipping AI Logic (Gemini models), CLI Agent Mode, and App Check in August 2026. Firebase is building an explicit agentic developer surface.

### Firebase — Firebase MCP Server — official server in firebase-tools with 30+ tools

- **Feature:** `mcp-agent-api`
- **Impact:** 🔴 strong (competitor gaining on LibreBase)
- **Confidence:** 85%
- **Source:** https://firebase.google.com/docs/ai-assistance/mcp-server
- **LibreBase delta:** Direct competitive signal: Firebase ships an official MCP server (in firebase-tools) supporting Claude Code, Cursor, Gemini CLI, Windsurf, VS Code Copilot. 30+ tools for managing, building, observing Firebase projects. Firebase is going all-in on agentic DX.

### Firebase — Firebase agent skills — portable modules for AI assistants (Claude Code, Codex, Cursor)

- **Feature:** `mcp-agent-api`
- **Impact:** 🔴 strong (competitor gaining on LibreBase)
- **Confidence:** 75%
- **Source:** https://firebase.google.com/docs/ai-assistance/agent-skills
- **LibreBase delta:** Watch: Firebase publishing agent skills — portable, self-contained modules of Firebase-specific knowledge for AI assistants. Complements the MCP server with token-efficient progressive disclosure. Pattern LibreBase should replicate.

### PocketBase — Community MCP servers for PocketBase: nestebe/pocketbase-mcp v1.0.0 (55 tools), mabeldata, Gaspechak, victormpa/PyPI

- **Feature:** `mcp-agent-api`
- **Impact:** 🔴 strong (competitor gaining on LibreBase)
- **Confidence:** 70%
- **Source:** https://github.com/nestebe/pocketbase-mcp/blob/main/CHANGELOG.md
- **LibreBase delta:** Watch: PocketBase itself has no official MCP server, but the community has built at least 4 third-party MCP servers (nestebe v1.0.0 with 55 tools, mabeldata, Gaspechak, victormpa on PyPI). Strong developer demand for PocketBase + MCP — LibreBase can win by shipping official first.

### Nhost — Nhost MCP service — open-source Go service exposing GraphQL via MCP

- **Feature:** `mcp-agent-api`
- **Impact:** 🔴 strong (competitor gaining on LibreBase)
- **Confidence:** 80%
- **Source:** https://nhost.io/blog/mcp-service
- **LibreBase delta:** Direct competitive signal: Nhost ships an open-source Go MCP service that exposes any Nhost project's GraphQL API through MCP. AI agents can query schemas, run GraphQL, manage migrations, set permissions. Pattern: BaaS + MCP = agentic backend.

### Nhost — Nhost MCP Server: Connect AI Tools to Your Backend — schemas, GraphQL, migrations, permissions

- **Feature:** `mcp-agent-api`
- **Impact:** 🔴 strong (competitor gaining on LibreBase)
- **Confidence:** 75%
- **Source:** https://nhost.io/blog/introducing-nhost-mcp-server
- **LibreBase delta:** Watch: Nhost MCP server lets AI tools like Cursor and Claude securely query schemas, run GraphQL, manage migrations, and set permissions. Nhost is positioning as an agentic GraphQL backend.

### Directus — Directus native MCP server — built-in, governed by default, same RBAC as human users

- **Feature:** `mcp-agent-api`
- **Impact:** 🔴 strong (competitor gaining on LibreBase)
- **Confidence:** 85%
- **Source:** https://directus.io/
- **LibreBase delta:** Direct competitive signal: Directus ships a native MCP server in-product. AI agents operate under the same role-based access control as human users — 'governed by default.' Connects Claude Desktop, Cursor, ChatGPT. LibreBase should match this governance story.

### Directus — Directus v11.15: Native Collaborative Editing, AI Assistant GA, One-Click Vercel Deployments

- **Feature:** `mcp-agent-api`
- **Impact:** 🔴 strong (competitor gaining on LibreBase)
- **Confidence:** 75%
- **Source:** https://directus.io/blog/directus-11-15-release
- **LibreBase delta:** Watch: Directus AI Assistant reaches GA in v11.15 with multi-provider support and real content awareness. Collaborative editing built into core. Deployment module for Vercel. AI is becoming a core DX pillar for Directus.

### Xano — Xano Q2 2026: Xano Agent, XanoScript GA, CLI, Sandbox, Error Logs Dashboard

- **Feature:** `mcp-agent-api`
- **Impact:** 🔴 strong (competitor gaining on LibreBase)
- **Confidence:** 80%
- **Source:** https://community.xano.com/product-updates/post/state-of-xano-q2-2026-h2PLnzEttXFee4O
- **LibreBase delta:** Watch: Xano shipping the most complete agentic backend story among no-code BaaS: Xano Agent (builds across entire backend), XanoScript GA (AI output maps to visual workflows), CLI GA, Sandbox environments, Developer MCP. This is the governance + agentic DX benchmark.

### Xano — Xano Developer MCP — AI agents get context to build in your Xano workspace

- **Feature:** `mcp-agent-api`
- **Impact:** 🔴 strong (competitor gaining on LibreBase)
- **Confidence:** 80%
- **Source:** https://www.xano.com/blog/ai-needs-a-governed-backend-we-built-it/
- **LibreBase delta:** Direct competitive signal: Xano Developer MCP gives AI coding agents context to build in your Xano workspace from local dev environment. Agents read, write, validate backend logic through XanoScript while routing every change through sandbox + deployment pipeline. Governance + agentic DX combined.

### Xano — Xano Knowledge v2.5 — governed agent context (AGENTS.md, Docs, Skills) native to workspace

- **Feature:** `mcp-agent-api`
- **Impact:** 🔴 strong (competitor gaining on LibreBase)
- **Confidence:** 75%
- **Source:** https://www.xano.com/blog/make-ai-build-exactly-how-you-want-it-to-build-introducing-knowledge-in-xano/
- **LibreBase delta:** Watch: Xano Knowledge feature treats agent context (AGENTS.md, Docs, Skills) as governed business logic — authored once, reviewed like code, versioned like function stacks, enforced by admins. Same library reaches local coding agents via CLI + Developer MCP. This is the governance pattern LibreBase should study.

### Railway — dev.new — Railway's agent that can build, preview, test, and deploy an app

- **Feature:** `mcp-agent-api`
- **Impact:** 🔴 strong (competitor gaining on LibreBase)
- **Confidence:** 70%
- **Source:** https://blog.railway.app/
- **LibreBase delta:** Watch: Railway building dev.new — an agent that can build, preview, test, and deploy an app from the same place. Railway is explicitly targeting the agentic development workflow.

### Fly.io — Fly.io: new CEO Scott Johnston, Sprites launch — semi-disposable compute for agents

- **Feature:** `mcp-agent-api`
- **Impact:** 🔴 strong (competitor gaining on LibreBase)
- **Confidence:** 75%
- **Source:** https://fly.io/blog/kurt-scott-money-sprites
- **LibreBase delta:** Watch: Fly.io re-focusing on Sprites (semi-disposable compute for agents) and appointing new CEO Scott Johnston. Fly.io explicitly targeting agentic workloads: 'An agent can one-shot a Fly.io deployment.' Agent-optimized infra is a growing thesis.

### Fly.io — Fly.io Managed Postgres — pgvector, PostGIS, 1TB storage, automatic HA

- **Feature:** `vector-embeddings`
- **Impact:** 🔴 strong (competitor gaining on LibreBase)
- **Confidence:** 65%
- **Source:** https://fly.io/docs/mpg
- **LibreBase delta:** Watch: Fly.io Managed Postgres includes pgvector (vector similarity search) and PostGIS (geospatial) as supported extensions. Competitive signal for vector/Postgres capabilities in the deployment/BaaS space.

### Heroku — Heroku AI: Claude 4.6, DeepSeek v3.2, Kimi K2.5, new standard plan for Managed Inference and Agents

- **Feature:** `mcp-agent-api`
- **Impact:** 🔴 strong (competitor gaining on LibreBase)
- **Confidence:** 80%
- **Source:** https://www.heroku.com/blog/new-models-and-flexible-standard-plan/
- **LibreBase delta:** Direct competitive signal: Heroku launching a standard plan for Managed Inference and Agents — single add-on, single API key, entire model catalogue (Claude 4.6, DeepSeek v3.2, Kimi K2.5, MiniMax M2.1, ZAI GLM 4.7). Heroku is building an explicit agentic AI platform layer.

## 📈 Feature Changes (today)

- **Fly.io** — `vector-embeddings` none → yes ⬆️
  - Daily scan 2026-09-11: strong — Fly.io Managed Postgres — pgvector, PostGIS, 1TB storage, automatic HA https://fly.io/docs/mpg

## 🔴 Where LibreBase Is WEAK (attack surface — competitor strong)

### Supabase — Supabase Series F — Multigres v0.1 alpha, scalable Postgres OS

- **Announced:** postgresql-db
- **Source:** https://supabase.com/blog/series-f
- **LibreBase delta:** Watch: Supabase raising Series F and shipping Multigres v0.1 alpha — a self-hostable scalable OS for Postgres with Vitess-grade horizontal scaling planned. Signals deepening Postgres investment.
- **Confidence:** 70%

### Supabase — Supabase MCP Server — official MCP server for AI agents

- **Announced:** mcp-agent-api
- **Source:** https://supabase.com/docs/guides/ai-tools/mcp
- **LibreBase delta:** Direct competitive signal: Supabase ships an official MCP server (mcp.supabase.com) giving AI agents structured access to projects. LibreBase must ship its own MCP server to stay competitive.
- **Confidence:** 85%

### Supabase — Supabase Assistant v2 — AI assistant in Dashboard with schema design, SQL, RLS, functions, triggers

- **Announced:** mcp-agent-api
- **Source:** https://supabase.com/blog/supabase-ai-assistant-v2
- **LibreBase delta:** Watch: Supabase Assistant v2 expands AI into schema design, RLS policies, Postgres functions/triggers, SQL-to-client conversion. AI is becoming a first-class Supabase DX surface.
- **Confidence:** 80%

### Appwrite — February and March product update: Realtime queries, Appwrite Skills, new database features

- **Announced:** mcp-agent-api
- **Source:** https://appwrite.io/blog/post/february-and-march-product-update-realtime-queries-appwrite-skills-and-new-database-features
- **LibreBase delta:** Watch: Appwrite shipping relationship queries, new text column types (varchar/text/mediumtext/longtext), Realtime channel helpers, and Appwrite Skills — explicit AI-coding-era tooling.
- **Confidence:** 75%

### Appwrite — July product update: Remote MCP server, Projects API, OAuth Device Authorization

- **Announced:** mcp-agent-api
- **Source:** https://appwrite.io/blog/post/july-product-update-remote-mcp-server-projects-api-and-more
- **LibreBase delta:** Direct competitive signal: Appwrite's MCP server is now a hosted remote server (mcp.appwrite.io) with OAuth — no local install required. AI tools get structured access to Appwrite projects + documentation. This is the gold standard for BaaS MCP UX.
- **Confidence:** 85%

### Firebase — August 2026: AI Logic, CLI Agent Mode, and App Check — top 6 Firebase updates

- **Announced:** mcp-agent-api
- **Source:** https://firebase.google.com/
- **LibreBase delta:** Watch: Firebase shipping AI Logic (Gemini models), CLI Agent Mode, and App Check in August 2026. Firebase is building an explicit agentic developer surface.
- **Confidence:** 70%

### Firebase — Firebase MCP Server — official server in firebase-tools with 30+ tools

- **Announced:** mcp-agent-api
- **Source:** https://firebase.google.com/docs/ai-assistance/mcp-server
- **LibreBase delta:** Direct competitive signal: Firebase ships an official MCP server (in firebase-tools) supporting Claude Code, Cursor, Gemini CLI, Windsurf, VS Code Copilot. 30+ tools for managing, building, observing Firebase projects. Firebase is going all-in on agentic DX.
- **Confidence:** 85%

### Firebase — Firebase agent skills — portable modules for AI assistants (Claude Code, Codex, Cursor)

- **Announced:** mcp-agent-api
- **Source:** https://firebase.google.com/docs/ai-assistance/agent-skills
- **LibreBase delta:** Watch: Firebase publishing agent skills — portable, self-contained modules of Firebase-specific knowledge for AI assistants. Complements the MCP server with token-efficient progressive disclosure. Pattern LibreBase should replicate.
- **Confidence:** 75%

### PocketBase — Community MCP servers for PocketBase: nestebe/pocketbase-mcp v1.0.0 (55 tools), mabeldata, Gaspechak, victormpa/PyPI

- **Announced:** mcp-agent-api
- **Source:** https://github.com/nestebe/pocketbase-mcp/blob/main/CHANGELOG.md
- **LibreBase delta:** Watch: PocketBase itself has no official MCP server, but the community has built at least 4 third-party MCP servers (nestebe v1.0.0 with 55 tools, mabeldata, Gaspechak, victormpa on PyPI). Strong developer demand for PocketBase + MCP — LibreBase can win by shipping official first.
- **Confidence:** 70%

### Nhost — Nhost MCP service — open-source Go service exposing GraphQL via MCP

- **Announced:** mcp-agent-api
- **Source:** https://nhost.io/blog/mcp-service
- **LibreBase delta:** Direct competitive signal: Nhost ships an open-source Go MCP service that exposes any Nhost project's GraphQL API through MCP. AI agents can query schemas, run GraphQL, manage migrations, set permissions. Pattern: BaaS + MCP = agentic backend.
- **Confidence:** 80%

### Nhost — Nhost MCP Server: Connect AI Tools to Your Backend — schemas, GraphQL, migrations, permissions

- **Announced:** mcp-agent-api
- **Source:** https://nhost.io/blog/introducing-nhost-mcp-server
- **LibreBase delta:** Watch: Nhost MCP server lets AI tools like Cursor and Claude securely query schemas, run GraphQL, manage migrations, and set permissions. Nhost is positioning as an agentic GraphQL backend.
- **Confidence:** 75%

### Directus — Directus native MCP server — built-in, governed by default, same RBAC as human users

- **Announced:** mcp-agent-api
- **Source:** https://directus.io/
- **LibreBase delta:** Direct competitive signal: Directus ships a native MCP server in-product. AI agents operate under the same role-based access control as human users — 'governed by default.' Connects Claude Desktop, Cursor, ChatGPT. LibreBase should match this governance story.
- **Confidence:** 85%

### Directus — Directus v11.15: Native Collaborative Editing, AI Assistant GA, One-Click Vercel Deployments

- **Announced:** mcp-agent-api
- **Source:** https://directus.io/blog/directus-11-15-release
- **LibreBase delta:** Watch: Directus AI Assistant reaches GA in v11.15 with multi-provider support and real content awareness. Collaborative editing built into core. Deployment module for Vercel. AI is becoming a core DX pillar for Directus.
- **Confidence:** 75%

### Xano — Xano Q2 2026: Xano Agent, XanoScript GA, CLI, Sandbox, Error Logs Dashboard

- **Announced:** mcp-agent-api
- **Source:** https://community.xano.com/product-updates/post/state-of-xano-q2-2026-h2PLnzEttXFee4O
- **LibreBase delta:** Watch: Xano shipping the most complete agentic backend story among no-code BaaS: Xano Agent (builds across entire backend), XanoScript GA (AI output maps to visual workflows), CLI GA, Sandbox environments, Developer MCP. This is the governance + agentic DX benchmark.
- **Confidence:** 80%

### Xano — Xano Developer MCP — AI agents get context to build in your Xano workspace

- **Announced:** mcp-agent-api
- **Source:** https://www.xano.com/blog/ai-needs-a-governed-backend-we-built-it/
- **LibreBase delta:** Direct competitive signal: Xano Developer MCP gives AI coding agents context to build in your Xano workspace from local dev environment. Agents read, write, validate backend logic through XanoScript while routing every change through sandbox + deployment pipeline. Governance + agentic DX combined.
- **Confidence:** 80%

### Xano — Xano Knowledge v2.5 — governed agent context (AGENTS.md, Docs, Skills) native to workspace

- **Announced:** mcp-agent-api
- **Source:** https://www.xano.com/blog/make-ai-build-exactly-how-you-want-it-to-build-introducing-knowledge-in-xano/
- **LibreBase delta:** Watch: Xano Knowledge feature treats agent context (AGENTS.md, Docs, Skills) as governed business logic — authored once, reviewed like code, versioned like function stacks, enforced by admins. Same library reaches local coding agents via CLI + Developer MCP. This is the governance pattern LibreBase should study.
- **Confidence:** 75%

### Railway — dev.new — Railway's agent that can build, preview, test, and deploy an app

- **Announced:** mcp-agent-api
- **Source:** https://blog.railway.app/
- **LibreBase delta:** Watch: Railway building dev.new — an agent that can build, preview, test, and deploy an app from the same place. Railway is explicitly targeting the agentic development workflow.
- **Confidence:** 70%

### Fly.io — Fly.io: new CEO Scott Johnston, Sprites launch — semi-disposable compute for agents

- **Announced:** mcp-agent-api
- **Source:** https://fly.io/blog/kurt-scott-money-sprites
- **LibreBase delta:** Watch: Fly.io re-focusing on Sprites (semi-disposable compute for agents) and appointing new CEO Scott Johnston. Fly.io explicitly targeting agentic workloads: 'An agent can one-shot a Fly.io deployment.' Agent-optimized infra is a growing thesis.
- **Confidence:** 75%

### Fly.io — Fly.io Managed Postgres — pgvector, PostGIS, 1TB storage, automatic HA

- **Announced:** vector-embeddings
- **Source:** https://fly.io/docs/mpg
- **LibreBase delta:** Watch: Fly.io Managed Postgres includes pgvector (vector similarity search) and PostGIS (geospatial) as supported extensions. Competitive signal for vector/Postgres capabilities in the deployment/BaaS space.
- **Confidence:** 65%

### Heroku — Heroku AI: Claude 4.6, DeepSeek v3.2, Kimi K2.5, new standard plan for Managed Inference and Agents

- **Announced:** mcp-agent-api
- **Source:** https://www.heroku.com/blog/new-models-and-flexible-standard-plan/
- **LibreBase delta:** Direct competitive signal: Heroku launching a standard plan for Managed Inference and Agents — single add-on, single API key, entire model catalogue (Claude 4.6, DeepSeek v3.2, Kimi K2.5, MiniMax M2.1, ZAI GLM 4.7). Heroku is building an explicit agentic AI platform layer.
- **Confidence:** 80%

## ⚪ Other (noise / new-competitor / neutral — logged for record)

- **Appwrite** — Announcing Init: Appwrite's launch week returns Aug 31 — Sep 4, 2026  *(noise / logged for record)*
  - https://appwrite.io/blog/post/init-august-2026
- **PocketBase** — PocketBase v0.40.2 released Sep 2, 2026 — active weekly release cadence *(noise / logged for record)*
  - https://github.com/pocketbase/pocketbase/releases?page=4
- **PocketBase** — PocketBase v0.38.1: superuser IP/CIDR whitelist, rate-limit IP exclusions, pb_data/.notify watcher *(noise / logged for record)*
  - https://hivebook.wiki/wiki/pocketbase-v0381-single-binary-realtime-backend-on-sqlite
- **Directus** — Directus v12 upcoming: major Studio refresh, native draft & publishing, AI-powered translation *(noise / logged for record)*
  - https://community.directus.io/t/everything-v12-upgrades-new-features-and-mscl-license/2237
- **Railway** — Railway Mobile App for Android — Aug 21, 2026 *(noise / logged for record)*
  - https://railway.app/changelog
- **Render** — Better pricing for fast-growing teams — new Pro and Scale plans, no seat fees *(Comparable — keep watching)*
  - https://render.com/blog/better-pricing-for-fast-growing-teams
- **Render** — Updated plans for Render workspaces — opt-in by Aug 1, 2026 *(Comparable — keep watching)*
  - https://render.com/changelog/updated-plans-for-render-workspaces
- **Heroku** — Fine-Grained Access Control available for all Heroku customers — Aug 21, 2026 *(Comparable — keep watching)*
  - https://www.heroku.com/blog/fine-grained-access-control-now-available-all-customers/
- **Heroku** — Heroku March 2026 Update: 1GB slug limits, longer build timeouts, CLI v11 (ESM/oclif v4) *(noise / logged for record)*
  - https://www.heroku.com/blog/march-2026-update/
- **AWS Amplify** — AWS Amplify: Node.js 24 support (May 2026), configurable build instance type, WAF GA *(noise / logged for record)*
  - https://docs.aws.amazon.com/amplify/latest/userguide/document-history.html
- **Koywe** — Koywe: international treasury platform / cross-border payments — NOT a BaaS competitor *(noise / logged for record)*
  - https://www.koywe.com/en
- **(new/unresolved)** — Butterbase — open-source BaaS with Postgres, auth, storage, functions, AI gateway, and built-in MCP server *(New competitor discovered)*
  - https://runany.dev/blog/butterbase-open-source-backend-as-a-service
- **(new/unresolved)** — InsForge 2.0 — AI-agent-first backend: MCP server + CLI + Skills, Postgres, auth, storage, compute, hosting *(New competitor discovered)*
  - https://dev.to/danieltechlab/insforge-teaches-ai-agents-to-run-your-backend-it-hasnt-learned-to-keep-postgres-alive-yet-1iaa

## 🔎 Queries run today

- AWS Amplify new features 2026 site:aws.amazon.com/amplify
- appwrite MCP agent 2026
- appwrite new features 2026 site:appwrite.io/blog
- directus AI features 2026
- directus MCP agent 2026
- directus new features 2026 site:directus.io
- firebase MCP agent 2026
- firebase new features 2026 site:firebase.google.com
- fly.io new features 2026 site:fly.io
- fly.io postgres 2026
- heroku new features 2026 site:heroku.com
- koywe new features 2026
- new backend-as-a-service 2026 agent MCP
- nhost MCP agent 2026
- pocketbase MCP agent 2026
- pocketbase new features 2026
- railway new features 2026 site:railway.app
- render new features 2026 site:render.com
- render pricing 2026
- supabase MCP server agent 2026
- supabase new features 2026 site:supabase.com/blog
- xano MCP agent 2026
- xano new features 2026 site:xano.com
