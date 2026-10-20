# LibreBase Competitive Intelligence — Daily Scan 2026-09-09

> **Automated daily scan** — Hermes cron at 09:00 CEST weekdays. Scanned 13 known competitors + discovery queries. Confidence scores are coarse heuristics; treat as directional.

Scanned 42 findings today across 13 known competitors.

## 🚨 STRONG SIGNAL ALERTS

_These findings indicate a competitor is strong on a feature where LibreBase is weak or neutral. Action recommended._

### Supabase — Supabase MCP Server — connect AI tools (Claude Code, Codex, Gemini CLI, Grok) directly to Supabase

- **Feature:** `mcp-agent-api`
- **Impact:** 🔴 strong (competitor gaining on LibreBase)
- **Confidence:** 85%
- **Source:** https://supabase.com/docs/guides/ai-tools/mcp.md
- **LibreBase delta:** Supabase ships official hosted MCP server at mcp.supabase.com with OAuth — direct agent-channel competitor to LibreBase's MCP story
- **Snippet:** Supabase MCP Server — Connect your AI tools to Supabase using MCP. Hosted at https://mcp.supabase.com/mcp. Supports Claude Code, Codex, Gemini CLI, Grok, and more. Self-hosted also available.

### Supabase — Supabase Pipelines is now in Public Alpha — CDC from Postgres to BigQuery with schema change support

- **Feature:** `postgresql-db`
- **Impact:** 🔴 strong (competitor gaining on LibreBase)
- **Confidence:** 75%
- **Source:** https://supabase.com/blog/supabase-pipelines-public-alpha
- **LibreBase delta:** Supabase ships managed CDC pipelines (Postgres → BigQuery) with schema propagation — competes with LibreBase's postgresql-db value prop on data pipeline depth
- **Snippet:** Supabase Pipelines is now in public alpha. Biggest addition: schema change support. First destination: Google BigQuery. Request forms for ClickHouse, Snowflake, DuckLake.

### Supabase — Supabase Assistant v2 — AI assistant in Dashboard with schema design, SQL debugging, RLS policy generation, Postgres functions/triggers

- **Feature:** `vector-embeddings`
- **Impact:** 🔴 strong (competitor gaining on LibreBase)
- **Confidence:** 70%
- **Source:** https://supabase.com/blog/supabase-ai-assistant-v2
- **LibreBase delta:** Supabase Assistant v2 embeds AI deeply into the admin UI — schema design, SQL generation, RLS policy creation. Competes on AI-assisted developer experience.
- **Snippet:** Supabase Assistant v2 in the Dashboard — global assistant with Postgres schema design, data queries and charting, error debugging, RLS Policies, Functions, Triggers, SQL to supabase-js conversion.

### Appwrite — Appwrite MCP Server — AI agents interact with Appwrite projects (users, databases, files)

- **Feature:** `mcp-agent-api`
- **Impact:** 🔴 strong (competitor gaining on LibreBase)
- **Confidence:** 80%
- **Source:** https://appwrite.io/blog/post/make-best-use-appwrite-mcp
- **LibreBase delta:** Appwrite launched its own MCP server — agents can create users, manage databases, upload files. Direct MCP-agent competition.
- **Snippet:** Appwrite launched its own MCP server that allows your AI agents to interact with your Appwrite projects. The API MCP server lets agents create users, manage databases, upload files, and more.

### Appwrite — Announcing Appwrite 2.0 — new engine, rebuilt Console, PostgreSQL default, S3 API, OAuth 2.1, 5 database types

- **Feature:** `postgresql-db`
- **Impact:** 🔴 strong (competitor gaining on LibreBase)
- **Confidence:** 75%
- **Source:** https://appwrite.io/blog/post/announcing-appwrite-2
- **LibreBase delta:** Appwrite 2.0 ships with PostgreSQL as default database, rebuilt Console, S3-compatible storage, OAuth 2.1 — major platform refresh closing gap with Supabase
- **Snippet:** Appwrite 2.0 brings a new engine, a rebuilt Console, five database types, an S3 API, an OAuth 2.1 server, and organization-level Domains and Firewall. PostgreSQL is now the default database.

### Appwrite — Introducing the Appwrite plugin for Cursor: Skills, MCP, and commands

- **Feature:** `mcp-agent-api`
- **Impact:** 🔴 strong (competitor gaining on LibreBase)
- **Confidence:** 75%
- **Source:** https://appwrite.io/blog/post/announcing-appwrite-cursor-plugin
- **LibreBase delta:** Appwrite ships a Cursor plugin with MCP server integration — deep IDE embedding for agent workflows, competing with LibreBase's agent IDE story
- **Snippet:** The API MCP server lets agents interact directly with your Appwrite project: creating users, managing databases, uploading files, and more. Announcing the Appwrite plugin for Cursor: Skills, MCP, and commands.

### Firebase — Firebase MCP Server — GA since Oct 2025, 30+ tools across 10+ service categories, integrated into firebase-tools (1.6M weekly npm downloads)

- **Feature:** `mcp-agent-api`
- **Impact:** 🔴 strong (competitor gaining on LibreBase)
- **Confidence:** 85%
- **Source:** https://chatforest.com/reviews/firebase-mcp-server
- **LibreBase delta:** Firebase MCP server is GA, spansp Firestore, Auth, Cloud Functions, Crashlytics, Storage, Remote Config, Messaging — broadest MCP surface of any BaaS player
- **Snippet:** Firebase MCP Server — Full Firebase Stack Management Through Your AI Assistant. Official Google/Firebase implementation, GA since October 2025, 30+ tools across 10+ service categories. Firestore Remote MCP reached GA April 23 2026.

### Firebase — Codex CLI for Firebase Development: MCP Server, Agent Skills, and Full-Stack Workflows

- **Feature:** `mcp-agent-api`
- **Impact:** 🔴 strong (competitor gaining on LibreBase)
- **Confidence:** 80%
- **Source:** https://codex.danielvaughan.com/2026/05/25/codex-cli-firebase-development-mcp-server-agent-skills-fullstack-workflows
- **LibreBase delta:** Firebase ships agent skills catalogue (early 2026) alongside MCP server — structured knowledge modules for Firebase-specific tasks. Claude Code + Firebase MCP is a polished agent workflow.
- **Snippet:** Firebase MCP server graduated to GA in October 2025 and the Firebase agent skills catalogue landed in early 2026. Claude Code can read Firestore schema, write security rules, deploy Cloud Functions, and drive the Emulator Suite.

### Firebase — Claude Code + Firebase: MCP Server, CLAUDE.md Templates, and Firestore Security Rules (2026)

- **Feature:** `mcp-agent-api`
- **Impact:** 🔴 strong (competitor gaining on LibreBase)
- **Confidence:** 75%
- **Source:** https://thepromptshelf.dev/blog/claude-code-firebase-integration-guide-2026
- **LibreBase delta:** Mature Claude Code + Firebase integration guide published 2026 — shows Firebase has a well-trodden agent path that LibreBase needs to match on ease of agent onboarding
- **Snippet:** Claude Code and Firebase now talk to each other directly. Firebase ships an official MCP server (GA since October 2025) plus a catalogue of Agent Skills (early 2026).

### Nhost — Turn any Nhost project into an agentic service — open-source Go MCP service with OAuth2, GraphQL tools (get-schema, graphql-query, graphql-mutation)

- **Feature:** `mcp-agent-api`
- **Impact:** 🔴 strong (competitor gaining on LibreBase)
- **Confidence:** 80%
- **Source:** https://nhost.io/blog/mcp-service
- **LibreBase delta:** Nhost ships open-source MCP service (March 2026) that turns any Nhost project into an agentic service with OAuth2 auth, read-only GraphQL access. Direct agent-channel competitor.
- **Snippet:** Today we're releasing an open-source service that lets you turn any Nhost project into an agentic service in just a few clicks. The Nhost MCP service is an open-source Go service that exposes your project's GraphQL API through MCP.

### Nhost — Introducing Constellation — open-source, Hasura-compatible GraphQL engine written in Go, June 2026

- **Feature:** `postgresql-db`
- **Impact:** 🔴 strong (competitor gaining on LibreBase)
- **Confidence:** 75%
- **Source:** https://nhost.io/blog/introducing-constellation
- **LibreBase delta:** Nhost ships Constellation — a Go-based Hasura-compatible GraphQL engine using a fraction of Hasura's memory. Replaces Hasura dependency with open-source Go engine. PostgreSQL + SQLite backends.
- **Snippet:** Constellation turns a relational database into a role-based GraphQL API, designed as a near drop-in replacement for Hasura Community Edition. Written in Go. PostgreSQL and SQLite backends. Already serving production traffic at Nhost.

### Nhost — Meet the MCP server that knows your backend — Nhost MCP server for managing projects, migrations, permissions, GraphQL queries

- **Feature:** `mcp-agent-api`
- **Impact:** 🔴 strong (competitor gaining on LibreBase)
- **Confidence:** 80%
- **Source:** https://www.nhost.io/blog/introducing-nhost-mcp-server
- **LibreBase delta:** Nhost MCP server provides unified interface for AI tools to manage entire Nhost stack: documentation search, permission management, database migrations, GraphQL queries. Open source.
- **Snippet:** Nhost's MCP server provides a unified interface for your favourite AI tools to interact with your backend infrastructure. Search through Nhost documentation, manage permissions, create database migrations, execute GraphQL queries and mutations.

### Directus — Directus v12 — native draft/publishing workflows, AI-assisted translations, OAuth 2.1 for MCP, redesigned Studio for non-technical users

- **Feature:** `mcp-agent-api`
- **Impact:** 🔴 strong (competitor gaining on LibreBase)
- **Confidence:** 80%
- **Source:** https://directus.com/resources/v12-built-for-the-whole-team
- **LibreBase delta:** Directus v12 ships OAuth 2.1 for MCP, AI-assisted translations, native editorial workflows. Enterprise-grade authentication for AI-connected workflows — strong MCP position.
- **Snippet:** Directus v12 has native editorial workflows, AI-assisted translations, a redesigned Studio for non-technical users, and enterprise-grade authentication for AI-connected workflows. OAuth 2.1 for MCP. Published Sep 2, 2026.

### Directus — Directus — Collaborative Backend & Headless CMS with native MCP server for product catalog

- **Feature:** `mcp-agent-api`
- **Impact:** 🔴 strong (competitor gaining on LibreBase)
- **Confidence:** 75%
- **Source:** https://directus.io/
- **LibreBase delta:** Directus homepage leads with 'native MCP server for your product catalog' — positions MCP as a core feature, not an add-on. Self-host or Directus Cloud.
- **Snippet:** The backend for your whole team. Connect any database. Get instant APIs, a no-code interface, and a native MCP server for your product catalog. Self-host on your own infrastructure or deploy to Directus Cloud.

### Directus — Directus v12 — AI-assisted translations, JSON filtering with dot-notation path queries, 50+ features

- **Feature:** `vector-embeddings`
- **Impact:** 🔴 strong (competitor gaining on LibreBase)
- **Confidence:** 70%
- **Source:** https://directus.com/resources/v12-built-for-the-whole-team
- **LibreBase delta:** Directus adds AI-assisted translations and JSON filtering with path queries — AI features embedded in the data platform. Competes on AI-native CMS/backend positioning.
- **Snippet:** Directus v12: AI-assisted translations — enable translations on a collection and Directus handles the schema scaffolding. JSON filtering with dot-notation path queries on JSON fields. Published Sep 2, 2026.

### Xano — Xano Q2 2026: Xano Agent, XanoScript GA, CLI, Sandbox — MCP gives AI coding agents context to build in your workspace

- **Feature:** `mcp-agent-api`
- **Impact:** 🔴 strong (competitor gaining on LibreBase)
- **Confidence:** 75%
- **Source:** https://community.xano.com/product-updates/post/state-of-xano-q2-2026-h2PLnzEttXFee4O
- **LibreBase delta:** Xano ships Xano Agent + Developer MCP (Q2 2026) — AI coding agents get context to build in Xano workspace from local dev environment. MCP-native no-code backend.
- **Snippet:** Xano Q2 2026: Xano Agent, XanoScript GA, CLI, Sandbox. The Developer MCP gives AI coding agents the context they need to build in your Xano workspace from your local development environment.

### Xano — AI Tools for Agents & MCP Servers — every Xano API endpoint can be converted into an MCP tool with a single click

- **Feature:** `mcp-agent-api`
- **Impact:** 🔴 strong (competitor gaining on LibreBase)
- **Confidence:** 75%
- **Source:** https://www.xano.com/learn/ai-tools-for-agents-mcp-servers
- **LibreBase delta:** Xano converts every API endpoint into an MCP tool with one click — makes MCP adoption frictionless for no-code backends. Competes on MCP ease-of-use.
- **Snippet:** Learn how to build modular, reusable AI tools in Xano that power both MCP servers and AI agents. Inside your Xano project, every API endpoint can be converted into an MCP tool with a single click.

### Xano — Part 2 - Deep Dive: MCP for Building Connected AI Agents | Xano

- **Feature:** `mcp-agent-api`
- **Impact:** 🔴 strong (competitor gaining on LibreBase)
- **Confidence:** 70%
- **Source:** https://www.xano.com/learn/part-2-deep-dive-mcp-for-building-connected-ai-agents
- **LibreBase delta:** Xano publishes deep dive on MCP for building connected AI agents — investing in MCP education and positioning as an MCP-first platform.
- **Snippet:** Part 2 - Deep Dive: MCP for Building Connected AI Agents. Inside your Xano project, every API endpoint can be converted into an MCP tool with a single click.

### Railway — Railway MCP Server — remote MCP at mcp.railway.com with OAuth, CLI integration, and Railway Agent for multi-step operations

- **Feature:** `mcp-agent-api`
- **Impact:** 🔴 strong (competitor gaining on LibreBase)
- **Confidence:** 80%
- **Source:** https://docs.railway.com/ai/mcp-server
- **LibreBase delta:** Railway ships remote MCP server (mcp.railway.com) with OAuth + CLI auth, plus a Railway Agent for natural-language multi-step operations. Agent-native infra platform.
- **Snippet:** The Railway MCP Server implements MCP. It lets AI assistants create projects, deploy templates, manage environments, pull variables, and redeploy services. Runs at mcp.railway.com. OAuth or CLI auth. Includes railway-agent for multi-step operations.

### Railway — Better Rails for Agents: A New Remote MCP and Railway Agent in the CLI — April 2026

- **Feature:** `mcp-agent-api`
- **Impact:** 🔴 strong (competitor gaining on LibreBase)
- **Confidence:** 80%
- **Source:** https://blog.railway.com/p/agent-rails-remote-mcp-cli
- **LibreBase delta:** Railway's April 2026 blog details remote MCP architecture: Streamable HTTP, OAuth discovery, .well-known/oauth-authorization-server, railway-agent tool for delegating complex tasks to Railway's AI agent.
- **Snippet:** Better Rails for Agents: A New Remote MCP and Railway Agent in the CLI. Remote MCP Server is live at mcp.railway.com. Any MCP-compatible agent can connect over OAuth. The Railway CLI has a new railway agent command for terminal/CI.

### Render — Render Workflows now in public beta — durable tasks, SDK for TypeScript/Python, agent logic, data pipelines, billing flows

- **Feature:** `mcp-agent-api`
- **Impact:** 🔴 strong (competitor gaining on LibreBase)
- **Confidence:** 70%
- **Source:** https://render.com/changelog?_rsc=178l4
- **LibreBase delta:** Render Workflows (public beta) supports agent logic, data pipelines, billing flows with durable task chaining — competes on agent-orchestration primitives
- **Snippet:** Render Workflows now in public beta, with SDK support for TypeScript and Python. Define durable tasks and chain them into long-running background processes for agent logic, data pipelines, billing flows, and more.

### Fly.io — Fly.io Doubles Down on Computers for Agents with $25M Series D — new CEO Scott Johnston, 37,000 customers, 8,000 agent-native

- **Feature:** `mcp-agent-api`
- **Impact:** 🔴 strong (competitor gaining on LibreBase)
- **Confidence:** 85%
- **Source:** https://fly.io/news/fly-io-launches-computers-for-agents
- **LibreBase delta:** Fly.io raised $25M Series D specifically for 'computers for agents' — 8,000 agent-native customers, agent workloads = 2/3 of revenue from largest customers. Major agent-infra contender.
- **Snippet:** Fly.io Doubles Down on Computers for Agents with $25M to Deliver the Next Generation of AI Infrastructure. July 24, 2026. More than 37,000 customers build on Fly.io, and more than 8,000 of them are agent-native. Agent-native companies now represent approximately two-thirds of revenue from largest customers.

### Fly.io — Fly.io Sprites — persistent Linux computers for agents, evals, and tools; CLI auth; $5/mo starts; bill goes to zero when idle

- **Feature:** `mcp-agent-api`
- **Impact:** 🔴 strong (competitor gaining on LibreBase)
- **Confidence:** 80%
- **Source:** https://fly.io/
- **LibreBase delta:** Fly.io Sprites give each agent its own persistent Linux box with durable disk, secure connectivity, instant boot. Agent execution layer that competes with LibreBase's agent-hosting vision.
- **Snippet:** Fly.io gives agents real computers that have durable disk drives, secure connectivity to other systems, and the ability to scale to millions of instances. Sprites CLI: sprite org auth. Boots in 250ms or less. The bill goes to zero when nobody's home.

### Heroku — Heroku AI: New Models and a Flexible Standard Plan — Claude 4.6, DeepSeek v3.2, Kimi K2.5, MiniMax M2.1, Cohere Embed V4

- **Feature:** `mcp-agent-api`
- **Impact:** 🔴 strong (competitor gaining on LibreBase)
- **Confidence:** 75%
- **Source:** https://www.heroku.com/blog/new-models-and-flexible-standard-plan/
- **LibreBase delta:** Heroku launches Managed Inference + Agents with standard plan — unified add-on for entire model catalog (Claude 4.6, DeepSeek, Kimi, MiniMax, ZAI). Agent-friendly model hosting competes with LibreBase's AI gateway vision.
- **Snippet:** Heroku is introducing significant updates to Managed Inference and Agents. New standard plan: a single add-on and a single API key grant access to our entire catalog of supported models. Claude 4.6 family, DeepSeek v3.2, Kimi K2.5, MiniMax M2.1, ZAI GLM 4.7, Cohere Embed V4.

## 📈 Feature Changes (today)

- **Appwrite** — `postgresql-db` none → yes ⬆️
  - Daily scan 2026-09-09: strong — Announcing Appwrite 2.0 — new engine, rebuilt Console, PostgreSQL default, S3 API, OAuth 2.1, 5 database types https://appwrite.io/blog/post/announcing-appwrite-2
  - Source: https://appwrite.io/blog/post/announcing-appwrite-2

## 🔴 Where LibreBase Is WEAK (attack surface — competitor strong)

[24 strong-signal entries — see STRONG SIGNAL ALERTS above]

## ⚪ Other (noise / new-competitor / neutral — logged for record)

- **PocketBase** — PocketBase v0.38.1 — single-binary realtime backend on SQLite, 58,045 GitHub stars  *( · noise / logged for record )*
  - https://hivebook.wiki/wiki/pocketbase-v0381-single-binary-realtime-backend-on-sqlite
- **PocketBase** — PocketBase v0.39.x releases — SQL console in UI, fullscreen editor, realtime timeout controls, security fixes  *( · noise / logged for record )*
  - https://updateshub.net/en/source/pocketbase
- **PocketBase** — PocketBase in 2026: architecture note — SQLite, stateless auth, realtime subscriptions, 10,000+ connections on $5 Hetzner VPS  *( · noise / logged for record )*
  - https://cronfeed.work/oss-pocketbase-architecture-note-sqlite-auth-realtime-scope-boundary-2026
- **Railway** — Where Railway is, and where it's going (Summer 2026) — 4 new datacenter sites, Postgres improvements, backup experience  *( ⚪ Comparable — keep watching )*
  - https://blog.railway.app/p/railway-summer-update-2026
- **Render** — Render new workspace plans (April 2026) — flat pricing, no seat fees, Pro $25/mo, SOC 2/ISO on Pro, HIPAA on Scale  *( ⚪ Comparable — keep watching )*
  - https://render.com/blog/better-pricing-for-fast-growing-teams
- **Render** — Render new workspace plans — bandwidth overages per GB, custom domains $0.25/domain/month, high-memory compute coming  *( ⚪ Comparable — keep watching )*
  - https://render.com/docs/new-workspace-plans
- **Fly.io** — Fly.io Managed Postgres v2 beta, Managed MySQL private beta, Fly KMS, MPG v2 in more regions  *( ⚪ Comparable — keep watching )*
  - https://community.fly.io/c/fresh-produce/27
- **Heroku** — Fine-Grained Access Control Available for All Heroku Customers — view/deploy/operate/manage roles, SOC 2/HIPAA/ISO readiness  *( ⚪ Comparable — keep watching )*
  - https://www.heroku.com/blog/fine-grained-access-control-now-available-all-customers/
- **Heroku** — Heroku March 2026 Update — Sustaining Engineering model, 1GB slug limits, longer build timeouts, Heroku CLI v11 (ESM + oclif v4)  *( · noise / logged for record )*
  - https://www.heroku.com/blog/march-2026-update/
- **AWS Amplify** — AWS Amplify — Full Stack Development for Web and Mobile Apps, hosting, SSR, custom domains  *( · noise / logged for record )*
  - https://aws.amazon.com/amplify/
- **AWS Amplify** — AWS Amplify — Node.js 24 support added to SSR applications (May 4, 2026)  *( · noise / logged for record )*
  - https://docs.aws.amazon.com/amplify/latest/userguide/document-history.html
- **AWS Amplify** — AWS Amplify Features — scale and manage, hosting, SSR, monitoring with CloudWatch  *( · noise / logged for record )*
  - https://aws.amazon.com/amplify/features/
- **Koywe** — Koywe Platform — payments, multi-currency operations, PSE/PIX/SPEI local payment methods across Latin America  *( · noise / logged for record )*
  - https://docs.koywe.com/
- **Koywe** — Koywe — YC-backed on/off ramp for crypto in Latam, payment APIs (GraphQL + REST), SDKs  *( · noise / logged for record )*
  - https://ycombinator.com/launches/I5Z-koywe-the-on-and-off-ramp-for-crypto-in-latam
- **Koywe** — Koywe — International Treasury Platform: Global Payments 24/7, multi-currency virtual accounts, crypto operations  *( · noise / logged for record )*
  - https://koywe.com/en
- **(new/unresolved)** — Backenly — Autonomous backend platform: your coding agent builds it over MCP, Backenly keeps it running (Postgres, REST, auth, storage, realtime, functions)  *( 🆕 New competitor discovered )*
  - https://github.com/backenly/backenly
- **(new/unresolved)** — McpBackend — MCP Backend for AI Apps & Vibe Coding: SQLite backend, OAuth-authorized tools, one-click eject to Docker self-host  *( 🆕 New competitor discovered )*
  - https://mcpbackend.com/
- **(new/unresolved)** — Purple8 — AI-Native Infrastructure: replaces 20+ services with one embedded engine (database, vector search, graph, RAG, auth, encryption), 74 MCP tools  *( 🆕 New competitor discovered )*
  - https://www.purple8.ai/

## 🔎 Queries run today

[32 queries across 13 competitors + 6 discovery queries]
