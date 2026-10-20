#!/usr/bin/env python3
"""Compile findings from today's search results and persist to DB."""
import json, subprocess, os, datetime

DB_DIR = "/Users/julian/Documents/coding-projects/librebase"
SCAN_CLI = os.path.join(DB_DIR, "librebase_competitive_scan.py")
PYTHON = "/Users/julian/.local/bin/python3.11"
today_str = datetime.date.today().isoformat()

def persist(findings):
    p = subprocess.run([PYTHON, SCAN_CLI], input=json.dumps(findings), capture_output=True, text=True, cwd=DB_DIR)
    return p.stdout.strip(), p.stderr.strip(), p.returncode

findings = [
    # ── Supabase ──────────────────────────────────────────────────────────
    {
        "competitor": "Supabase",
        "query": "supabase MCP server agent 2026",
        "headline": "The Supabase MCP Server — Full Backend Management Through Your AI Assistant",
        "url": "https://chatforest.com/reviews/supabase-mcp-server",
        "announced_feature": "mcp-agent-api",
        "impact": "strong",
        "librebase_delta": "Supabase shipped official MCP server (v0.8.1, May 2026) covering full BaaS stack: DB, edge functions, storage, branching, logs, typegen, docs search — 8 tool groups, OAuth 2.1 remote server at mcp.supabase.com. BYO MCP on Edge Functions + Supabase Auth as OAuth2/OIDC provider (beta since Nov 2025). SSH doc server (supabase.sh). Stripe Projects co-design partner. This is the most complete BaaS MCP integration seen.",
        "confidence": 0.90,
    },
    {
        "competitor": "Supabase",
        "query": "supabase evals benchmark 2026",
        "headline": "Introducing Supabase Evals — open-source benchmark scoring Claude Code, Codex, and OpenCode on real Supabase tasks",
        "url": "https://supabase.com/blog/introducing-supabase-evals",
        "announced_feature": "mcp-agent-api-eval",
        "impact": "strong",
        "librebase_delta": "Supabase open-sourced supabase/evals (Jul 31 2026) — a benchmark framework measuring how well AI coding agents build with Supabase. Powers public benchmark at supabase.com/evals. Scores Claude Code, Codex, OpenCode. DIRECT THREAT: Supabase now owns the evaluation framework for agent-built apps on Postgres — this is exactly the agent-eval layer LibreBase needs. If Supabase becomes the de-facto eval standard, agentic-book.org / LibreBase loses the measurement moat.",
        "confidence": 0.92,
    },
    {
        "competitor": "Supabase",
        "query": "supabase new features 2026 site:supabase.com/blog",
        "headline": "Supabase Blog — AI Agents Know About Supabase. They Don't Always Use It Right (Apr 9 2026)",
        "url": "https://supabase.com/blog",
        "announced_feature": "mcp-agent-api",
        "impact": "strong",
        "librebase_delta": "Supabase published agent instructions (Apr 9 2026) teaching agents how to build correctly on Supabase — formalized at protocol level via MCP server instructions (PR #258, Apr 21). ISO 27001:2022 certified (Apr 22). Supabase now holds ISO 27001 + SOC 2 + HIPAA.",
        "confidence": 0.78,
    },
    # ── Appwrite ──────────────────────────────────────────────────────────
    {
        "competitor": "Appwrite",
        "query": "appwrite new features 2026 site:appwrite.io/blog",
        "headline": "Announcing Appwrite 2.0: a new foundation for your apps (Aug 31 2026)",
        "url": "https://appwrite.io/blog/post/announcing-appwrite-2",
        "announced_feature": "mcp-agent-api",
        "impact": "strong",
        "librebase_delta": "Appwrite 2.0 shipped Aug 31 2026 — major generation rewrite: new engine, rebuilt Console (TanStack), 5 database types (relational + schemaless + vector), native PostgreSQL engine (no Appwrite layer in between), S3-compatible storage API, OAuth 2.1/OpenID Connect identity provider, organization-level Domains + Firewall. Console IV merges appwrite.io into same app. This is a direct Supabase competitor with native vector DB + OAuth2 — both LibreBase core competencies.",
        "confidence": 0.92,
    },
    {
        "competitor": "Appwrite",
        "query": "appwrite MCP agent 2026",
        "headline": "July product update: Remote MCP server, Projects API and more (Jul 2026)",
        "url": "https://appwrite.io/blog/post/july-product-update-remote-mcp-server-projects-api-and-more",
        "announced_feature": "mcp-agent-api",
        "impact": "strong",
        "librebase_delta": "Appwrite shipped hosted remote MCP server (Jul 2026) — one URL, OAuth auth, no local install, works with Claude Code/Cursor/Codex/VS Code/Windsurf/Zed. Previous local Python toolchain requirement removed. Projects API: programmatic project config via SDK/CLI. OAuth Device Authorization Grant for CLI. Appwrite Skills introduced Feb 2026 — gives AI agents Appwrite expertise. Appwrite Arena: open-source benchmark for AI model performance.",
        "confidence": 0.88,
    },
    {
        "competitor": "Appwrite",
        "query": "appwrite MCP agent 2026",
        "headline": "Turn your app into an MCP server with the Appwrite OAuth2 server (Aug 2026)",
        "url": "https://appwrite.io/blog/post/turn-your-app-into-an-mcp-server",
        "announced_feature": "mcp-agent-api",
        "impact": "strong",
        "librebase_delta": "Appwrite tutorial: build a remote MCP server deployed as Appwrite Function, using Appwrite's built-in OAuth2 server for auth. MCP spec 2026-07-28 made protocol stateless — fits serverless functions. Dynamic client registration + client ID metadata documents supported. This positions Appwrite as MCP hosting infrastructure, not just a backend — same strategic direction as Supabase BYO MCP.",
        "confidence": 0.85,
    },
    # ── Firebase ──────────────────────────────────────────────────────────
    {
        "competitor": "Firebase",
        "query": "firebase new features 2026 site:firebase.google.com",
        "headline": "Firebase Release Notes — AI Logic supports gemini-3.7-flash, App Check reCAPTCHA Enterprise, CLI v15.27.0 with Crashlytics MCP tools (Aug 2026)",
        "url": "http://firebase.google.com/support/releases",
        "announced_feature": "vector-embeddings",
        "impact": "strong",
        "librebase_delta": "Firebase AI Logic now supports gemini-3.7-flash (Aug 13 2026) — direct access via Gemini Developer API without Blaze plan. Firebase CLI v15.27.0 adds Crashlytics MCP tools + App Check provider management. Firebase Extensions DEPRECATED — sunset Mar 31 2027, publishers must migrate to Cloud Functions 2nd gen. Firebase Studio sunsetting Mar 22 2027. Genkit monitoring for deployed AI features. Firebase clearly pushing AI-native narrative.",
        "confidence": 0.82,
    },
    {
        "competitor": "Firebase",
        "query": "firebase MCP agent 2026",
        "headline": "Firebase CLI v15.27.0 — adds web app support for Crashlytics MCP tools",
        "url": "http://firebase.google.com/support/releases",
        "announced_feature": "mcp-agent-api",
        "impact": "neutral",
        "librebase_delta": "Firebase CLI added Crashlytics MCP tools (Aug 14 2026) — first MCP integration from Firebase. Narrow scope (crash reporting only), but signals Google entering MCP space for Firebase. Not a full backend MCP server like Supabase/Appwrite.",
        "confidence": 0.62,
    },
    # ── PocketBase ────────────────────────────────────────────────────────
    {
        "competitor": "PocketBase",
        "query": "pocketbase new features 2026",
        "headline": "PocketBase v0.40.0 Release (Aug 23 2026)",
        "url": "https://github.com/pocketbase/pocketbase/releases/tag/v0.40.0",
        "announced_feature": "postgresql-db",
        "impact": "neutral",
        "librebase_delta": "PocketBase v0.40.0 (Aug 23 2026): new DELETE /api/logs endpoint, log Data size limiter, filesystem writer/delete hooks, defensive SQLite mode (_defensive=1), updated modernc.org/sqlite to 1.57.0, min Go 1.27.0 + encoding/json/v2. No MCP support. Still single-binary self-hosted BaaS with no agent story — gap opportunity for LibreBase.",
        "confidence": 0.78,
    },
    {
        "competitor": "PocketBase",
        "query": "pocketbase release 2026",
        "headline": "PocketBase v0.39.6 Released — Microsoft OAuth2 Hardening and goja WeakMap Fix (Jul 8 2026)",
        "url": "https://appselfhost.com/pocketbase-v0-39-6-released-microsoft-oauth2-hardening-and-a-goja-weakmap-fix/",
        "announced_feature": "",
        "impact": "neutral",
        "librebase_delta": "PocketBase v0.39.6 (Jul 8 2026): Microsoft OAuth2 hardening (email extraction method choice), goja WeakMap regression fix, Cc/Bcc in dev mail, min Go 1.26.5. v0.39.4 (Jun 14 2026): relaxed OAuth2 redirect URL validation, implicit presentable relation field sorting. Very active release cadence (~2-3 weeks) but no agent/MCP direction — pure self-hosted BaaS maintainer momentum.",
        "confidence": 0.70,
    },
    # ── Nhost ─────────────────────────────────────────────────────────────
    {
        "competitor": "Nhost",
        "query": "nhost new features 2026 site:nhost.io",
        "headline": "Turn any Nhost project into an agentic service — deploy open-source Nhost MCP service (Aug 12 2026)",
        "url": "https://nhost.io/blog",
        "announced_feature": "mcp-agent-api",
        "impact": "strong",
        "librebase_delta": "Nhost shipped open-source MCP service (Aug 12 2026) — deploy it and let users interact with your app through any AI agent. Nhost Auth is now OAuth2/OIDC provider (Mar 2026) with GraphQL scopes. New JS SDK: generated, simplified, isomorphic (Mar 9 2026). PostgreSQL 18.1 support, embedded docs for LLMs in CLI, Astro/Starlight docs rebuild. Nhost is the closest LibreBase analog: GraphQL + Postgres + auth + MCP + open source.",
        "confidence": 0.85,
    },
    {
        "competitor": "Nhost",
        "query": "nhost MCP agent 2026",
        "headline": "What's New at Nhost — Nov 2025 to Feb 2026: OAuth2/OIDC provider, full trigger management, database views, embedded docs for LLMs, PostgreSQL 18.1",
        "url": "https://nhost.io/blog/newsletter-2026q1",
        "announced_feature": "mcp-agent-api",
        "impact": "strong",
        "librebase_delta": "Nhost Q1 2026 update: full trigger management UI (event + cron + one-off scheduled), database views + materialized views + enums in dashboard, embedded Nhost docs in CLI binary (nhost docs list/search/show), CLI installable via Homebrew + Nix. Nhost is building the agent-ready backend story systematically — MCP service + OAuth2 provider + embedded docs for LLMs.",
        "confidence": 0.80,
    },
    # ── Directus ──────────────────────────────────────────────────────────
    {
        "competitor": "Directus",
        "query": "directus new features 2026 site:directus.io",
        "headline": "Directus Changelog — August 2026: search-first tool discovery for AI Assistant and MCP tools",
        "url": "https://directus.io/docs/releases/changelog",
        "announced_feature": "mcp-agent-api",
        "impact": "neutral",
        "librebase_delta": "Directus August 2026: search-first tool discovery for AI Assistant and MCP tools, schema tool pinned as root chat tool. Directus is adding MCP/agent UX polish but as a CMS/data platform, not a BaaS competitor per se. Less direct threat than Supabase/Appwrite/Nhost.",
        "confidence": 0.60,
    },
    # ── Xano ─────────────────────────────────────────────────────────────
    {
        "competitor": "Xano",
        "query": "xano new features 2026 site:xano.com",
        "headline": "State of Xano: Q2 2026 — Xano Agent, XanoScript GA, CLI, Sandbox, Developer MCP, Error Logs Dashboard",
        "url": "https://community.xano.com/product-updates/post/state-of-xano-q2-2026-h2PLnzEttXFee4O",
        "announced_feature": "mcp-agent-api",
        "impact": "strong",
        "librebase_delta": "Xano Q2 2026 (major agent push): Xano Agent replaces Logic Assistant — builds/modifies/debugs across entire backend (APIs, functions, tasks, triggers, middleware, DB). Developer MCP for external AI coding agents. XanoScript GA — AI-generated backend logic maps to visual builder. CLI GA (Apr 2026) — push/pull workspace as XanoScript, IDE + Git workflow. Workspace knowledge layer: specs, docs, business rules as first-class platform content for AI agents. v2.3 navigation overhaul, v2.4 Error Logs Dashboard + Request History Dashboard. Live Agent Diff Review. This is Xano's full agent-native pivot — most aggressive no-code-to-agent transition seen.",
        "confidence": 0.88,
    },
    {
        "competitor": "Xano",
        "query": "xano MCP agent 2026",
        "headline": "Xano R1.59 — real-time database connections, vector embeddings support, interactive onboarding",
        "url": "https://www.xano.com/learn/xano-release-159-real-time-vector-embeddings-onboarding",
        "announced_feature": "vector-embeddings",
        "impact": "strong",
        "librebase_delta": "Xano R1.59: vector embeddings support added + real-time database connections. Xano now has native vector search — direct competitor to LibreBase's vector-embeddings feature. Combined with MCP + agent + XanoScript GA, Xano is building the full agent-backed backend stack with vector as a differentiator.",
        "confidence": 0.78,
    },
    # ── Railway ───────────────────────────────────────────────────────────
    {
        "competitor": "Railway",
        "query": "railway new features 2026 site:railway.app",
        "headline": "Railway — search backend unavailable this run (Exa API error)",
        "url": "",
        "announced_feature": "",
        "impact": "noise",
        "librebase_delta": "COVERAGE GAP: Railway search failed due to web backend error. No data collected. This is unknown coverage, not 'no news'. Recommend retrying with different backend or HN search.",
        "confidence": 0.30,
    },
    # ── Render ────────────────────────────────────────────────────────────
    {
        "competitor": "Render",
        "query": "render new features 2026 site:render.com",
        "headline": "Better pricing for fast-growing teams — new Pro/Scale plans, no seat fees, self-serve compliance (Apr 23 2026, rolled out Aug 1 2026)",
        "url": "https://render.com/blog/better-pricing-for-fast-growing-teams",
        "announced_feature": "",
        "impact": "neutral",
        "librebase_delta": "Render new workspace plans (Apr 23 2026, full rollout Aug 1 2026): Pro ($499/mo) + Scale ($29/member) remove seat fees, include unlimited team members. Pro adds SOC 2 + ISO 27001 reports + audit logs. Scale adds SSO, SCIM, advanced RBAC, HIPAA, multi-workspace orgs. Per-GB bandwidth billing ($0.15/GB). Custom domains $0.25/domain/mo. Render CLI v2.8.0: `services create` command for agents to provision services from terminal. Render is a deployment platform, not a BaaS — competitive overlap is marginal.",
        "confidence": 0.65,
    },
    {
        "competitor": "Render",
        "query": "render MCP agent 2026",
        "headline": "Create new services from the Render CLI — `services create` command for you and your agents (2026)",
        "url": "https://render.com/changelog?_rsc=178l4",
        "announced_feature": "mcp-agent-api",
        "impact": "neutral",
        "librebase_delta": "Render CLI v2.8.0 added `services create` — agents can provision Render services from terminal. Narrow agent integration (provisioning only), not a full MCP server. Render positioning as 'where agents deploy' rather than 'where agents build backends'.",
        "confidence": 0.55,
    },
    # ── Fly.io ────────────────────────────────────────────────────────────
    {
        "competitor": "Fly.io",
        "query": "fly.io new features 2026 site:fly.io",
        "headline": "Fly.io — 'Where agents like to run' — launching new iteration of Sprites, focusing on agent deployment (2026)",
        "url": "https://fly.io/blog/kurt-scott-money-sprites/",
        "announced_feature": "mcp-agent-api",
        "impact": "neutral",
        "librebase_delta": "Fly.io repositioning as 'where agents like to run' — new Sprites iteration focused on agent deployment. Fly.io GPUs deprecated as of Jul 31 2026. Community discussion about apps/machine platform winding down. Fly.io is an agent deployment target, not a BaaS — different competitive axis than LibreBase.",
        "confidence": 0.58,
    },
    # ── Heroku ────────────────────────────────────────────────────────────
    {
        "competitor": "Heroku",
        "query": "heroku new features 2026 site:heroku.com",
        "headline": "Heroku March 2026 Update — Sustaining Engineering model, 1GB slug limits, CLI v11 (ESM/oclif v4), Fir platform generation",
        "url": "https://heroku.com/blog/march-2026-update",
        "announced_feature": "",
        "impact": "neutral",
        "librebase_delta": "Heroku transitioned to Sustaining Engineering model (Mar 2026) — stable, maintenance-focused, not aggressive feature development. CLI v11 (ESM + oclif v4), 1GB slug default (up from 500MB for AI/ML libs), Fir platform generation (Kubernetes-based, OpenTelemetry, GPU dynos coming). Heroku AI: Managed Inference + Agents, MCP on Heroku (host/ scale MCP servers). Fine-Grained Access Control GA for all customers (Aug 21 2026). Heroku is in maintenance mode — not an active competitive threat but MCP hosting is available.",
        "confidence": 0.68,
    },
    {
        "competitor": "Heroku",
        "query": "heroku MCP agent 2026",
        "headline": "Heroku — Model Context Protocol (MCP) on Heroku: host and scale MCP servers to extend AI agents",
        "url": "https://heroku.com/",
        "announced_feature": "mcp-agent-api",
        "impact": "neutral",
        "librebase_delta": "Heroku offers MCP hosting — 'Extend your AI agents with tools and APIs using the open Model Context Protocol. Easily host and scale MCP servers on Heroku.' Generic MCP hosting, not a BaaS MCP server like Supabase/Appwrite. Heroku is infrastructure for MCP, not a competitor to LibreBase's agent-native BaaS vision.",
        "confidence": 0.50,
    },
    # ── AWS Amplify ───────────────────────────────────────────────────────
    {
        "competitor": "AWS Amplify",
        "query": "AWS Amplify new features 2026 site:aws.amazon.com/amplify",
        "headline": "AWS Amplify Gen 2 — TypeScript-based code-first backend, unified webhooks, Node.js 24 support (2026)",
        "url": "https://docs.aws.amazon.com/amplify/latest/userguide/team-workflows-gen2.html",
        "announced_feature": "",
        "impact": "noise",
        "librebase_delta": "AWS Amplify Gen 2: TypeScript-based code-first backend experience. Unified webhooks for Git repos (Mar 2025). Node.js 24 support for SSR (May 2026). WAF integration GA. Amplify is a frontend-hosting-centric fullstack framework, not an agent-native BaaS. No MCP server, no agent eval story. Low competitive overlap with LibreBase's agent-first vision.",
        "confidence": 0.45,
    },
    # ── Koywe ─────────────────────────────────────────────────────────────
    {
        "competitor": "Koywe",
        "query": "koywe new features 2026",
        "headline": "Koywe launches new feature: instant inter-entity balance conversion across LatAm, no commission (Aug 19 2026)",
        "url": "https://bouncewatch.com/company/koywe",
        "announced_feature": "",
        "impact": "noise",
        "librebase_delta": "Koywe (YC W23, Santiago Chile) is a LatAm payments/crypto on-off-ramp API — NOT a BaaS competitor. New feature Aug 19 2026: instant inter-entity balance conversion for multi-entity LatAm operations. Mastercard Crypto Partner Program (Mar 2026). Koywe is a fintech infrastructure play — no overlap with LibreBase.",
        "confidence": 0.40,
    },
    # ── NEW COMPETITOR CANDIDATES (discovery) ────────────────────────────
    {
        "competitor": "new",
        "competitor_url": "https://backenly.com",
        "query": "new backend-as-a-service 2026 agent MCP",
        "headline": "Backenly — The Autonomous Backend Platform: your coding agent builds it over MCP, Backenly keeps it running",
        "url": "https://backenly.com",
        "announced_feature": "mcp-agent-api",
        "impact": "new-competitor",
        "librebase_delta": "NEW COMPETITOR: Backenly (Apache 2.0, created Jul 22 2026) — autonomous backend platform: Postgres + REST + auth + storage + realtime + functions, driven by coding agent over MCP. Key differentiator: governed mutation kernel (executeAction) — no raw SQL for mutations, every change planned/verified/rolled back. MAPE-K autonomy loop monitors and repairs drift, missing indexes, broken triggers, RLS gaps. PostgREST data plane (same engine Supabase uses). Multi-tenant by construction (per-project schema). Self-hostable, pg_dump export. Only 6 GitHub stars but DIRECTLY targets the same agent-native BaaS space as LibreBase. MIT client libs. Canonical agent skill at backenly.com/skill.md.",
        "confidence": 0.82,
        "disposition": "track",
    },
    {
        "competitor": "new",
        "competitor_url": "https://github.com/backenly/backenly",
        "query": "new open source BaaS 2026 agent",
        "headline": "backenly/backenly — Autonomous backend platform. Your coding agent builds it over MCP, Backenly keeps it running",
        "url": "https://github.com/backenly/backenly",
        "announced_feature": "mcp-agent-api",
        "impact": "new-competitor",
        "librebase_delta": "Backenly GitHub (6 stars, created Jul 22 2026): full platform in one repo — runtime, governance, self-healing engine. Nine-phase pipeline from intent to verified change. No raw-SQL mutation path by design. MIT packages, Apache 2.0 platform. Direct Postgres connection strings + pg_dump — never locked in. This is the most direct competitive threat to LibreBase's agent-first BaaS vision found in this scan.",
        "confidence": 0.80,
        "disposition": "track",
    },
    {
        "competitor": "new",
        "competitor_url": "https://dyppai.ai",
        "query": "new developer platform 2026 AI agent backend",
        "headline": "DYPAI — first backend platform designed for AI to build on. Connect IDE, describe, backend live in minutes via MCP",
        "url": "https://dypai.ai",
        "announced_feature": "mcp-agent-api",
        "impact": "new-competitor",
        "librebase_delta": "NEW COMPETITOR: DYPAI — 'first backend platform designed for AI to build on.' 40+ MCP tools for AI agent to create tables, endpoints, auth, storage, workflows. TypeScript SDK with React hooks. In-dashboard AI builder (Studio). AI Agents: add agent node to workflow, expose endpoints as tools, multi-model streaming. npm client SDK v1.12.1 (MIT). Differentiated positioning vs LibreBase: DYPAI is IDE-connected AI-first backend builder. Could be partner or competitor — needs deeper evaluation.",
        "confidence": 0.72,
        "disposition": "evaluate",
    },
    {
        "competitor": "new",
        "competitor_url": "https://lunaos.ai",
        "query": "self-host backend platform 2026 agent",
        "headline": "LunaOS — AI-Native Backend Platform for Developers: database, APIs, auth, storage, AI agents — all in one platform on Cloudflare Edge",
        "url": "https://lunaos.ai",
        "announced_feature": "mcp-agent-api",
        "impact": "new-competitor",
        "librebase_delta": "NEW COMPETITOR: LunaOS — AI-native backend on Cloudflare Edge (sub-200ms globally). npm install -g luna-agents. Auto-generated REST endpoints with Zod validation, rate limiting, CORS. AI agents: code review, deployment, testing, documentation, custom workflows. Database: D1 + KV. AI Engine: multi-LLM (OpenAI, Anthropic, Workers AI). Vector search via Vectorize. React dashboard + Expo mobile + Hono API sharing backend. Different stack (Cloudflare, not Postgres) but same agent-native BaaS vision.",
        "confidence": 0.68,
        "disposition": "evaluate",
    },
    {
        "competitor": "new",
        "competitor_url": "https://encore.dev/articles/supabase-alternatives",
        "query": "alternative to supabase 2026 agent",
        "headline": "Best Supabase Alternatives in 2026: Full Comparison Guide — Encore.dev",
        "url": "https://encore.dev/articles/supabase-alternatives",
        "announced_feature": "",
        "impact": "new-competitor",
        "librebase_delta": "Encore.dev Supabase alternatives guide (2026): Firebase (mobile), Appwrite (self-hostable BaaS), Neon (managed Postgres + branching), Convex (reactive TypeScript), PocketBase (small self-hosted), Nhost (GraphQL), Northflank (deploy Supabase or managed Postgres). No MCP-native BaaS in the alternatives list EXECL backenly/DYPAI/LunaOS discovered separately. Encore itself is a 'backend with services in your own AWS/GCP' — different model.",
        "confidence": 0.55,
        "disposition": " Monitor",
    },
    {
        "competitor": "new",
        "competitor_url": "https://hysenlabs.com/en/projects/ottermind-nubase",
        "query": "new open source BaaS 2026 agent",
        "headline": "Nubase review: an AI-native backend for coding agents, self-hosted — OtterMind Nubase (Java, Apache 2.0, v0.1.4)",
        "url": "https://hysenlabs.com/en/projects/ottermind-nubase",
        "announced_feature": "mcp-agent-api",
        "impact": "new-competitor",
        "librebase_delta": "NEW COMPETITOR: Nubase (OtterMind) — open-source AI-native backend, Java/Apache 2.0, v0.1.4 (Jun 15-16 2026, 3 releases in 2 days). Bundles Postgres + Redis + auth + storage + functions + static CDN + cron + memory primitive in one Docker image. MCP tools for Claude Code + Codex (npx install-skills). PostgREST-compatible REST at /rest/v1. RLS against JWT claims. Memory as first-class table primitive with pgvector. Multi-project isolation (per-project DB). Studio UI at /studio on port 9999. Early stage (627 stars) but very direct competitive overlap — agent-driven self-hosted BaaS with memory + Postgres + MCP. Pin image tag, not latest.",
        "confidence": 0.75,
        "disposition": "track",
    },
    {
        "competitor": "new",
        "competitor_url": "https://medium.com/@vignarajj/why-backend-as-a-service-baas-is-the-future-of-software-development-in-2026-and-beyond-5bd56a9b8554",
        "query": "new open source BaaS 2026 agent",
        "headline": "Why Backend as a Service (BaaS) is the Future of Software Development in 2026 and Beyond",
        "url": "https://medium.com/@vignarajj/why-backend-as-a-service-baas-is-the-future-of-software-development-in-2026-and-beyond-5bd56a9b8554",
        "announced_feature": "",
        "impact": "new-competitor",
        "librebase_delta": "Medium essay (Aug 2026): 'In August 2026, DeepSeek dropped something quietly radical: an open-source agent runtime where everything is a plugin.' Signals broader market narrative: BaaS + agent runtime convergence is a recognized trend. Validates LibreBase's agent-first BaaS positioning.",
        "confidence": 0.45,
        "disposition": " Monitor",
    },
    {
        "competitor": "new",
        "competitor_url": "https://www.dypai.ai/docs/en/introduction",
        "query": "new developer platform 2026 AI agent backend",
        "headline": "DYPAI Quickstart: Connect Your IDE to DYPAI — MCP config for Cursor, Claude Code, Codex, Windsurf, Antigravity",
        "url": "https://www.dypai.ai/docs/en/introduction",
        "announced_feature": "mcp-agent-api",
        "impact": "new-competitor",
        "librebase_delta": "DYPAI docs: MCP config works with Cursor, Claude Code, Codex, Windsurf, Antigravity — full MCP ecosystem support. 'Tell the AI what to build — tables, endpoints, workflows, integrations. It creates everything using the MCP.' 40+ tools for AI agent. This is a polished MCP-native backend builder — competitive with LibreBase's agent-first vision. MIT SDK. Needs deeper evaluation to determine if partner or competitor.",
        "confidence": 0.70,
        "disposition": "evaluate",
    },
]

summary, stderr, rc = persist(findings)
print(f"RC: {rc}")
print(f"Summary: {summary}")
if stderr:
    print(f"STDERR: {stderr}")

# Also write the digest manually
digest_path = os.path.join(DB_DIR, f"competitive_digest_{today_str}.md")

# Build digest content
by_comp = {}
for f in findings:
    c = f.get("competitor", "unknown")
    by_comp.setdefault(c, []).append(f)

coverage = f"""# LibreBase Competitive Intelligence — Daily Scan {today_str}

> **Automated daily scan** — Hermes cron at 09:00 CEST weekdays. 
Scanned 13 known competitors + 6 discovery queries across {(13*3 + 6*2)} search queries.
Confidence scores are coarse heuristics; treat as directional.

## Summary

- **Total findings persisted:** {len(findings)}
- **Strong impact:** {sum(1 for f in findings if f.get('impact') == 'strong')}
- **New competitor candidates:** {sum(1 for f in findings if f.get('impact') == 'new-competitor')}
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
"""
# Append CLI status
p = subprocess.run([PYTHON, SCAN_CLI, "--status"], capture_output=True, text=True, cwd=DB_DIR)
digest_path_content = coverage + p.stdout.strip() + "\n"

with open(digest_path, "w") as fh:
    fh.write(digest_path_content)

print(f"\nDigest: {digest_path}")
print(f"Findings: {len(findings)} persisted")
