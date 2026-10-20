#!/usr/bin/env /Users/julian/Documents/coding-projects/librebase/.venv/bin/python3
"""Assemble findings from web_search results and persist to scan CLI."""
import json, subprocess, os, sys, datetime

DB_DIR = "/Users/julian/Documents/coding-projects/librebase"
SCAN_CLI = os.path.join(DB_DIR, "librebase_competitive_scan.py")
PYTHON = "/Users/julian/Documents/coding-projects/librebase/.venv/bin/python3"

def classify(title, desc):
    """Keyword → feature + impact mapping."""
    t = (title + desc).lower()
    if any(k in t for k in ["mcp", "agent", "agentic", "agent sdk", "agent api"]):
        return "mcp-agent-api", "strong"
    if any(k in t for k in ["eval", "benchmark", "agent performance", "agent test"]):
        return "mcp-agent-api", "strong"
    if any(k in t for k in ["ai", "vector", "embedding", "pgvector", "ml", "llm"]):
        return "vector-embeddings", "strong"
    if any(k in t for k in ["edge function", "serverless function", "cloud function"]):
        return "edge-functions", "neutral"
    if any(k in t for k in ["pipeline", "etl", "cdc", "data pipeline", "bigquery"]):
        return "postgresql-db", "strong"
    if any(k in t for k in ["pricing", "price", "cost", "plan", "tier"]):
        return "billing-plans", "neutral"
    return "", "noise"

def make(comp, query, title, desc, url, extra=None):
    feat, impact = classify(title, desc)
    base = {
        "competitor": comp,
        "query": query,
        "headline": title,
        "url": url,
        "announced_feature": feat,
        "impact": impact,
        "raw_snippet": f"{title} — {(desc or '')[:300]}",
        "confidence": 0.65 if feat else 0.45,
    }
    if feat:
        base["librebase_delta"] = f"Watch: {title}"
    if extra:
        base.update(extra)
    return base

findings = []

# ═══════════════════════════════════════════════
# SUPABASE (3 strongest)
# ═══════════════════════════════════════════════
findings.append(make(
    "Supabase",
    "supabase MCP server agent 2026",
    "The Supabase MCP Server — Full Backend Management Through Your AI Assistant",
    "Official Supabase MCP server (supabase-community/supabase-mcp, 2.6K stars, v0.8.1). Covers 8 tool groups: database, edge functions, storage, branching, debugging, dev, docs, account. Hosted at mcp.supabase.com with OAuth 2.1. v0.8.0 (Apr 30) added RLS advisory in list_tables + server instructions support. Supabase ISO 27001:2022 certified Apr 22.",
    "https://chatforest.com/reviews/supabase-mcp-server",
    {"announced_feature": "mcp-agent-api", "impact": "strong", "confidence": 0.85}
))

findings.append(make(
    "Supabase",
    "supabase evals benchmark 2026",
    "Introducing Supabase Evals",
    "Supabase open-sourced supabase/evals (Jul 31, 2026) — benchmark framework testing how well AI agents (Claude Code, Codex, OpenCode) build with Supabase. Runs against real Supabase environments via MCP server + CLI. Published benchmark scores: Claude Code/Opus 5 = 91% total, Codex/GPT-5.6 = 80%, OpenCode/Kimi K3 = 78%. Skills loaded → agents check docs more consistently. Agents still hand-write migrations despite declarative schemas.",
    "https://supabase.com/blog/supabase-evals",
    {"announced_feature": "mcp-agent-api", "impact": "strong", "confidence": 0.80}
))

findings.append(make(
    "Supabase",
    "supabase pricing changes 2026",
    "Supabase Pricing History: 9 Changes Detected",
    "Supabase raised Team plan from $2 to $10 (+400%) on May 22, 2026. July 27, 2026: Pro +10 changes, Team +7 changes. Usage-based overages for MAUs ($0.00325/MAU), DB storage ($0.125/GB), egress ($0.09/GB), Edge Functions ($2/M), Messages ($2.50/M). Team plan now $599/mo self-serve. Organization-based billing rolled out Sep 2023, fully self-serve Team Plan as of 2026.",
    "https://getpulsesignal.com/changes/supabase",
    {"announced_feature": "billing-plans", "impact": "neutral", "confidence": 0.70}
))

# ═══════════════════════════════════════════════
# APPWRITE (3)
# ═══════════════════════════════════════════════
findings.append(make(
    "Appwrite",
    "appwrite new features 2026 site:appwrite.io/blog",
    "Announcing an improved Appwrite Databases experience",
    "Appwrite shipped TablesDB API — a parallel relational model with tables, rows, columns. New spreadsheet-like data management UI. Full backward compatibility maintained.",
    "https://appwrite.io/blog/post/announcing-appwrite-databases-new-ui",
    {"announced_feature": "postgresql-db", "impact": "neutral", "confidence": 0.60}
))

findings.append(make(
    "Appwrite",
    "appwrite MCP agent 2026",
    "Add any custom authentication flow to your applications",
    "Appwrite blog highlights custom auth flows, Appwrite Functions ecosystem improvements, new ML-optimized runtime for Appwrite Cloud, and new mobile SDK. Appwrite 2.0 brought PostgreSQL as default DB, rebuilt Console, S3 API, OAuth 2.1 server, organization-level Domains and Firewall.",
    "https://appwrite.io/blog/categories/products",
    {"announced_feature": "mcp-agent-api", "impact": "noise", "confidence": 0.45}
))

findings.append(make(
    "Appwrite",
    "appwrite pricing 2026",
    "Appwrite 2.0: a new foundation for your apps",
    "Appwrite 2.0 released with rebuilt Console, PostgreSQL as default database, combined worker topology (16 containers vs 33), S3-compatible Storage API, OAuth 2.1 server, organization-level Domains and Firewall. Appwrite 2.1 added S3 API and AutoGravity to self-hosted, TikTok and Kakao sign-in.",
    "https://appwrite.io/blog/post/announcing-appwrite-2",
    {"announced_feature": "postgresql-db", "impact": "neutral", "confidence": 0.60}
))

# ═══════════════════════════════════════════════
# FIREBASE (3)
# ═══════════════════════════════════════════════
findings.append(make(
    "Firebase",
    "firebase MCP agent 2026",
    "Firebase MCP Server — Full Firebase Stack Management Through Your AI Assistant",
    "Firebase MCP server (official Google, GA Oct 2025) ships inside firebase-tools (1.6M+ weekly npm downloads). 50+ tools across 12 service categories: Firestore, Auth, Storage, Cloud Functions, Crashlytics, FCM, App Hosting, Remote Config, Realtime DB, Data Connect. Firestore Remote MCP reached GA Apr 23, 2026. CLI v15.13.0 added SSE mode. Firebase Agent Skills catalogue landed early 2026. Google Cloud Next '26: Firebase is one of 50+ official Google MCP servers.",
    "https://chatforest.com/reviews/firebase-mcp-server",
    {"announced_feature": "mcp-agent-api", "impact": "strong", "confidence": 0.85}
))

findings.append(make(
    "Firebase",
    "firebase new features 2026 site:firebase.google.com",
    "Firebase Studio sunset and project migration",
    "Firebase Studio sunset announced Mar 19, 2026; migration tools rolling out. New workspace creation disabled Jun 22, 2026. Firebase Community page lists 2026 themes: AI Logic (Gemini models), CLI Agent Mode, App Check. Firebase pricing changes effective Sep 1, 2026. Unity SDK v13.12.0 released Jun 3, 2026 with new Analytics features.",
    "https://firebase.google.com/docs/studio/migrating-project",
    {"announced_feature": "mcp-agent-api", "impact": "neutral", "confidence": 0.55}
))

findings.append(make(
    "Firebase",
    "google cloud firebase updates 2026",
    "Codex CLI for Firebase Development: MCP Server, Agent Skills, and Full-Stack Workflows",
    "Firebase MCP server exposes 50+ tools via stdio; SSE mode available since v15.16.0. Firebase Agent Skills: firebase-auth-basics, firebase-firestore-standard, firebase-app-hosting-basics, firebase-ai-logic-basics, developing-genkit-js. Install: npx skills add firebase/agent-skills --agent=codex. Community alternative: gannonh/firebase-mcp (224 stars, v1.4.9) with HTTP transport + file upload tools.",
    "https://codex.danielvaughan.com/2026/05/25/codex-cli-firebase-development-mcp-server-agent-skills-fullstack-workflows",
    {"announced_feature": "mcp-agent-api", "impact": "strong", "confidence": 0.80}
))

# ═══════════════════════════════════════════════
# POCKETBASE (3)
# ═══════════════════════════════════════════════
findings.append(make(
    "PocketBase",
    "pocketbase release 2026",
    "PocketBase v0.40.0 release notes",
    "PocketBase v0.40.0 released Aug 23, 2026. Added DELETE /api/logs endpoint, log.Data size limiting (~16KB truncation), filesystem.NewWriter + OnNewWriter/OnDelete hooks. Updated modernc.org/sqlite to 1.57.0 with _defensive=1 DSN parameter (SQLite defensive mode). Bumped min Go to 1.27.0, migrated to encoding/json/v2.",
    "https://whatsnew.fyi/product/pocketbase/releases/v0.40.0",
    {"announced_feature": "postgresql-db", "impact": "noise", "confidence": 0.55}
))

findings.append(make(
    "PocketBase",
    "pocketbase new features 2026",
    "PocketBase Cloud Changelog — August 2026",
    "PocketBase Cloud shipped Aug 5: self-service account deletion, About/Security pages. Aug 4: named compute selection (Compute 2 — Frankfurt). Aug 3: usage/performance metrics per instance, webhook+authorization hardening. Jul 30: pb_migrations and pb_public can now be updated on running instances via zip upload. Public status page launched Aug 11.",
    "https://pocketbasecloud.com/changelog",
    {"announced_feature": "postgresql-db", "impact": "noise", "confidence": 0.55}
))

findings.append(make(
    "PocketBase",
    "pocketbase roadmap 2026",
    "What is PocketBase? The Single-File Backend Explained",
    "PocketBase packs database, auth, realtime, file storage into one ~15MB binary. PocketBase Cloud offers managed hosting. 2026 blog: scaling from MVP to production (Mar 5), migrating from Firebase to PocketBase Cloud (Feb 1), multi-instance hosting (Jan 20). Migrating from Firebase guide positions PocketBase as Firebase cost-alternative.",
    "https://pocketbasecloud.com/blog",
    {"announced_feature": "postgresql-db", "impact": "noise", "confidence": 0.45}
))

# ═══════════════════════════════════════════════
# NHOST (3)
# ═══════════════════════════════════════════════
findings.append(make(
    "Nhost",
    "nhost MCP agent 2026",
    "Turn Any Nhost Project into an Agentic Service",
    "Nhost released an open-source service to turn any Nhost project into an agentic service in a few clicks. Nhost is a managed Postgres backend with GraphQL (Hasura-compatible), Auth, Storage, serverless Functions. Also shipping Constellation — open-source Hasura-compatible GraphQL engine in Go using ~90% less memory than Hasura.",
    "https://nhost.io/blog/mcp-service",
    {"announced_feature": "mcp-agent-api", "impact": "strong", "confidence": 0.75}
))

findings.append(make(
    "Nhost",
    "nhost new features 2026 site:nhost.io",
    "What's New at Nhost — Nov 2025 to Feb 2026",
    "Nhost Q1 2026 newsletter: Nhost Auth is now an OAuth2/OIDC provider. Significant platform changes across Postgres, GraphQL, Auth, and Storage. Nhost combines Hasura GraphQL with auth and storage on a Postgres-backed stack.",
    "https://nhost.io/blog/newsletter-2026q1",
    {"announced_feature": "mcp-agent-api", "impact": "neutral", "confidence": 0.55}
))

findings.append(make(
    "Nhost",
    "nhost GraphQL 2026",
    "Constellation: Hasura-Compatible GraphQL in Go",
    "Nhost open-sourced Constellation — a Hasura-compatible GraphQL engine written in Go, production-tested, using ~90% less memory than Hasura. This is a significant engineering investment in the GraphQL layer of their backend platform.",
    "https://nhost.io/blog/introducing-constellation",
    {"announced_feature": "graphql", "impact": "neutral", "confidence": 0.65}
))

# ═══════════════════════════════════════════════
# DIRECTUS (3)
# ═══════════════════════════════════════════════
findings.append(make(
    "Directus",
    "directus AI features 2026",
    "Directus v11.16: Global Draft Versions, Multimodal AI, and Smarter Deployments",
    "Directus v11.16 (Mar 10, 2026): AI Assistant now multimodal — can see images and PDFs (OpenAI, Anthropic, Google Gemini). Global draft versions across every collection. Deployment module with role-based access + Vercel/Netlify webhooks (real-time status). json() function for JSON field extraction across PostgreSQL, MySQL, SQLite, MSSQL, Oracle, CockroachDB.",
    "https://directus.io/blog/directus-11-16-release",
    {"announced_feature": "vector-embeddings", "impact": "strong", "confidence": 0.70}
))

findings.append(make(
    "Directus",
    "directus new features 2026 site:directus.io",
    "Directus v11.15: Native Collaborative Editing, AI Assistant Goes GA",
    "Directus v11.15 (Feb 2026): Native collaborative editing built into core (WebSocket + Redis). AI Assistant ships to GA with multi-provider support (OpenAI, Anthropic, Google Gemini, Ollama-compatible) and real content awareness. Deployment module for Vercel one-click deploys from Data Studio. Google Cloud Next '26-era updates through Jul 2026: Directus 12.2.0 with Tiptap WYSIWYG, POST /utils/import endpoint, schema snapshot scoping.",
    "https://directus.io/blog/directus-11-15-release",
    {"announced_feature": "vector-embeddings", "impact": "strong", "confidence": 0.75}
))

findings.append(make(
    "Directus",
    "directus MCP agent 2026",
    "AI | Directus Docs — External AI Tools: MCP Server",
    "Directus ships a Model Context Protocol (MCP) server connecting external AI tools (Claude Desktop, ChatGPT, Cursor) to Directus. Plus AI Translations for content fields with glossary/style guide support. Directus v12 upcoming: native draft & publishing, redesigned Studio, AI-powered translation tools. New MSCL license for self-hosted — 3 seats, 5 flows, no SSO on free tier (controversial change).",
    "https://directus.io/docs/guides/ai",
    {"announced_feature": "mcp-agent-api", "impact": "strong", "confidence": 0.70}
))

# ═══════════════════════════════════════════════
# XANO (3)
# ═══════════════════════════════════════════════
findings.append(make(
    "Xano",
    "xano MCP agent 2026",
    "Xano Q2 2026: Xano Agent, XanoScript GA, CLI, Sandbox, and Error Logs Dashboard",
    "Xano 2.3/2.4 (Q2 2026): Xano Agent replaces Logic Assistant — builds/modifies/debugs entire backend via natural language using XanoScript + Developer MCP. Xano CLI GA (Apr 2026) — push/pull workspaces as XanoScript, Git integration, Claude Code/Cursor/Copilot/Codex integration. Sandbox environments for safe AI-assisted dev. Error Logs Dashboard (v2.4) — workspace-wide error grouping. MCP Builder SSE transport deprecated in v2.6.",
    "https://community.xano.com/product-updates/post/state-of-xano-q2-2026-h2PLnzEttXFee4O",
    {"announced_feature": "mcp-agent-api", "impact": "strong", "confidence": 0.80}
))

findings.append(make(
    "Xano",
    "xano new features 2026 site:xano.com",
    "Xano 2.0: The First Production-Grade Backend That Moves at AI Speed",
    "Xano 2.0 launch (May 13, 2026): Three build modalities — AI (Logic Assistant → Xano Agent), Visual (Canvas View node-based builder), Code (XanoScript). XanoScript lets devs write backend logic in code synchronized with visual interface. Xano MCP + VS Code Extension for IDE-native backend development. Git Sync + Version Diff for GitHub/GitLab. CEO Prakash Chandran: 'from no-code backend to AI governance layer.'",
    "https://xano.com/news/xano-2",
    {"announced_feature": "mcp-agent-api", "impact": "strong", "confidence": 0.80}
))

findings.append(make(
    "Xano",
    "xano no-code backend 2026 updates",
    "What's New — Xano Updates (Aug 19, 2026)",
    "Aug 19, 2026: XanoScript MCP Server Tools now carry per-tool connection settings/authentication through code-defined MCP servers. Xano CLI v1.2.0: workflow_test run returns failing exit code on failure for CI. New: Azure AI Foundry Model Host for Xano Agents. Knowledge & Skills: Markdown editing for knowledge files, tenant deployment of knowledge+skills, export. Hash indexes on XanoScript. Agent visual diff review — side-by-side XanoScript + visual diff.",
    "https://docs.xano.com/updates",
    {"announced_feature": "mcp-agent-api", "impact": "strong", "confidence": 0.75}
))

# ═══════════════════════════════════════════════
# RAILWAY (3)
# ═══════════════════════════════════════════════
findings.append(make(
    "Railway",
    "railway new features 2026 site:railway.app",
    "Where Railway is, and where it's going (Summer 2026)",
    "Railway Summer 2026 update: platform direction and roadmap. Railway offers automated service discovery, fast networking, any protocol support. Changelog active through Aug 21, 2026.",
    "https://blog.railway.app/p/railway-summer-update-2026",
    {"announced_feature": "", "impact": "noise", "confidence": 0.45}
))

findings.append(make(
    "Railway",
    "railway MCP agent 2026",
    "Announcing: dev.new, an agent that can build, preview, test, and deploy an app",
    "Railway announced dev.new — an AI agent that can build, preview, test, and deploy apps from a single place. Railway account required to deploy code. This positions Railway as an agent-native deployment platform.",
    "https://blog.railway.app/",
    {"announced_feature": "mcp-agent-api", "impact": "strong", "confidence": 0.70}
))

findings.append(make(
    "Railway",
    "railway database 2026",
    "Railway Features",
    "Railway provides automated service discovery, blazing fast networking, support for any protocol. Platform features focused on deployment + database hosting. Railway Mobile App for Android shipped Aug 21, 2026.",
    "https://railway.app/features",
    {"announced_feature": "postgresql-db", "impact": "neutral", "confidence": 0.50}
))

# ═══════════════════════════════════════════════
# RENDER (3)
# ═══════════════════════════════════════════════
findings.append(make(
    "Render",
    "render new features 2026 site:render.com",
    "Better pricing for fast-growing teams",
    "Render launched new Pro and Scale plans with no seat fees, more self-serve compliance features, fairer billing for bandwidth. New compute plans: memory-optimized with higher RAM/CPU ratios, new 12-CPU tier for web services. Network-isolated environments, private links for AWS connectivity.",
    "https://render.com/blog/better-pricing-for-fast-growing-teams",
    {"announced_feature": "billing-plans", "impact": "neutral", "confidence": 0.60}
))

findings.append(make(
    "Render",
    "render pricing 2026",
    "Platforms with a real free tier for developers in 2026",
    "Render provides free web services, static sites, and PostgreSQL databases deployable directly from Git. Connected to GitHub. Positioned as one of the platforms with a real free tier in 2026.",
    "https://render.com/articles/platforms-with-a-real-free-tier-for-developers-in-2026",
    {"announced_feature": "billing-plans", "impact": "neutral", "confidence": 0.50}
))

findings.append(make(
    "Render",
    "render database 2026",
    "Changelog - Render",
    "Render changelog: new compute plans for Render services including memory-optimized plans with higher RAM/CPU ratios and new 12-CPU tier for web services. Platform features by plan: network-isolated environments, private links, additional member roles (Contributor, Viewer, Billing).",
    "https://render.com/changelog",
    {"announced_feature": "postgresql-db", "impact": "neutral", "confidence": 0.50}
))

# ═══════════════════════════════════════════════
# FLY.IO (3)
# ═══════════════════════════════════════════════
findings.append(make(
    "Fly.io",
    "fly.io MCP agent 2026",
    "Turn And Face The Strange — Fly.io Sprites for Agents",
    "Fly.io launched new iteration of Sprites — 'computers for agents.' Semi-disposable cows with 100GB durable disk, metered utility billing (meter doesn't run when idle), instant checkpoint-and-restore. New: Sprite Block Device (SBD) enabling drive forking — clone millions of times from a template. Connectors: authenticated requests to other systems without exfiltrating secrets. Scott Johnston tagged in as CEO. Fly.io raising more money, focusing company on Sprites + agent problem.",
    "https://fly.io/blog/kurt-scott-money-sprites",
    {"announced_feature": "mcp-agent-api", "impact": "strong", "confidence": 0.85}
))

findings.append(make(
    "Fly.io",
    "fly.io postgres 2026",
    "Managed Postgres — Fly.io Docs",
    "Fly.io Managed Postgres: HA with automatic failover, automatic backups/recovery, performance monitoring, resource scaling, 24/7 support. pgvector extension for vector similarity search, PostGIS for geospatial. Plans: Basic $38/mo (1GB), Starter $72/mo (2GB), Launch $282/mo (8GB), Scale $962/mo (32GB), Performance $1,922/mo (64GB). Starting Feb 2026: inter-region private network usage charged at same rate as Machines.",
    "https://fly.io/docs/mpg",
    {"announced_feature": "postgresql-db", "impact": "neutral", "confidence": 0.65}
))

findings.append(make(
    "Fly.io",
    "fly.io new features 2026 site:fly.io",
    "Easier certs behind Cloudflare, BYO certs, and other goodies",
    "Fly.io shipped: _fly-ownership TXT record for domain verification (sidesteps IPv6/Cloudflare issues), custom certificate imports (fly certs import, Cloudflare origin CA support, up to 15-year certs), certificate changes propagate to all edges immediately, new Machines API endpoints for certificate management. Dashboard deploy improvements: copy logs, npm run build error messages, Fly.io branch created before build step.",
    "https://community.fly.io/t/easier-certs-behind-cloudflare-byo-certs-and-other-goodies/27146",
    {"announced_feature": "edge-functions", "impact": "neutral", "confidence": 0.55}
))

# ═══════════════════════════════════════════════
# HEROKU (3)
# ═══════════════════════════════════════════════
findings.append(make(
    "Heroku",
    "heroku new features 2026 site:heroku.com",
    "An Update on Heroku — Sustaining Engineering Model",
    "Heroku transitioning to sustaining engineering model focused on stability, security, reliability, and support. Fir generation: more than 500 dynos per space, enhanced networking firewalls coming. VPC peering and Private Spaces DNS Service Discovery still To Be Added for Fir. Cedar still has more features than Fir in some areas.",
    "https://www.heroku.com/blog/an-update-on-heroku/",
    {"announced_feature": "", "impact": "noise", "confidence": 0.50}
))

findings.append(make(
    "Heroku",
    "heroku postgres 2026",
    "Heroku March 2026 Update",
    "Heroku March 2026: Longer build timeouts for complex builds. Heroku CLI v11 — complete architectural move to ESM and oclif v4, faster execution and better maintainability. Heroku Fir generally available with expanded dyno options, Cloud Native Buildpacks, observability integration.",
    "https://www.heroku.com/blog/march-2026-update/",
    {"announced_feature": "postgresql-db", "impact": "neutral", "confidence": 0.50}
))

findings.append(make(
    "Heroku",
    "heroku pricing 2026",
    "Heroku Fir: Dive into the New Platform Capabilities",
    "Heroku Fir GA: significantly expanded dyno options, Cloud Native Buildpacks, robust observability integration. Heroku Postgres with continuous protection, rollback, high availability. Feature parity gaps between Fir and Cedar: VPC peering, DNS service discovery still missing on Fir.",
    "https://www.heroku.com/blog/heroku-fir-generally-available-new-platform-capabilities/",
    {"announced_feature": "postgresql-db", "impact": "neutral", "confidence": 0.50}
))

# ═══════════════════════════════════════════════
# AWS AMPLIFY (3)
# ═══════════════════════════════════════════════
findings.append(make(
    "AWS Amplify",
    "AWS Amplify new features 2026 site:aws.amazon.com/amplify",
    "AWS Amplify Features — Full Stack Development",
    "AWS Amplify: full-stack TypeScript, frontend DX for AWS. Zero-config Next.js/Nuxt deployments via CloudFront Global Edge Network. Git-based CI/CD with PR previews. Amplify Studio visual backend config. Auth (Cognito), Storage (S3), Data (DynamoDB/AppSync), Functions (Lambda), AI/ML (Sagemaker). Node.js 24 support added May 4, 2026.",
    "https://aws.amazon.com/amplify/features/",
    {"announced_feature": "vector-embeddings", "impact": "neutral", "confidence": 0.55}
))

findings.append(make(
    "AWS Amplify",
    "AWS Amplify AI features 2026",
    "Document history for AWS Amplify — May 4, 2026",
    "AWS Amplify docs updated May 4, 2026: Node.js 24 support added for SSR apps. Configurable build instance type feature (CPU/memory/disk selection). AWS WAF integration GA (Mar 26, 2025). Skew protection for Amplify deployments (Mar 10, 2025). Unified webhooks for Git repositories (Mar 10, 2025). SSR Compute role for AWS resource access (Feb 17, 2025).",
    "https://docs.aws.amazon.com/amplify/latest/userguide/document-history.html",
    {"announced_feature": "vector-embeddings", "impact": "neutral", "confidence": 0.50}
))

findings.append(make(
    "AWS Amplify",
    "AWS Amplify pricing 2026",
    "AWS Amplify Pricing",
    "AWS Amplify pricing: Standard Instance (8GB/4vCPU) $0.01/min build, Large (16GB/8vCPU) $0.025/min, XLarge (72GB/36vCPU) $0.10/min. Data storage $0.023/GB/mo on CDN. Data transfer $0.15/GB. SSR requests $0.30/M. SSR duration $0.20/GB-hour. WAF $15/mo per app + WAF costs. Free Tier: 1,000 build minutes/mo, 5GB CDN storage, 15GB data transfer, 500K SSR requests, 100GB-hour SSR duration. Up to $200 AWS Free Tier credits for new customers (from Jul 15, 2025).",
    "https://aws.amazon.com/amplify/pricing/",
    {"announced_feature": "billing-plans", "impact": "neutral", "confidence": 0.55}
))

# ═══════════════════════════════════════════════
# KOYWE (3)
# ═══════════════════════════════════════════════
findings.append(make(
    "Koywe",
    "koywe new features 2026",
    "Koywe Platform — Payments, Multi-Currency, Crypto",
    "Koywe Platform: payment collection (PSE, PIX, SPEI, local methods), multi-currency operations across LATAM. Crypto on/off ramp (USDC, ETH, BTC, 8 networks). Multi-currency virtual accounts (COP, BRL, MXN, CLP, USD, EUR). Koywe CLI v0.14.1: 142 commands, 26 with --schema flag, designed for human devs + AI agents (Claude Code). Policy system for BALANCE_TRANSFER and MFA-gated operations. Documentation updated Jul 7, 2026.",
    "https://docs.koywe.com/en",
    {"announced_feature": "mcp-agent-api", "impact": "noise", "confidence": 0.45}
))

findings.append(make(
    "Koywe",
    "koywe backend as a service 2026",
    "Koywe fortalece su expansión regional y suma Bolivia",
    "Koywe expanded to Bolivia (8th market: Chile, Peru, Colombia, Mexico, Brazil, Argentina, US, Bolivia). Processed $2.16B in international transactions since 2023, projects >$1.04B in 2026. Stablecoin B2B payments expansion to Asia planned for 2027. YC-backed, $5M Seed (Aug 2024) from Franklin Templeton, Goodwater Capital, SeaX Ventures, Tantauco Ventures.",
    "https://startupslatam.com/koywe-fortalece-su-expansion-regional-y-suma-bolivia-a-su-red-de-pagos-transfronterizos/",
    {"announced_feature": "billing-plans", "impact": "noise", "confidence": 0.40}
))

findings.append(make(
    "Koywe",
    "koywe MCP agent 2026",
    "Se vienen cositas: primera transacción no custodia firmada por un agente (Codex) usando la API de Koywe",
    "Koywe LinkedIn (Mar 24, 2026): First non-custodial transaction signed by an agent (Codex) using Koywe API. Koywe has 60-70 employees (+30% YoY), $7.8M total funding. Headquartered in Santiago, Chile. 7-country workforce distribution. Koywe CLI designed for AI agents with structured JSON envelopes on every command.",
    "https://www.linkedin.com/posts/koywe_activity-7442230457099837441-ab37",
    {"announced_feature": "mcp-agent-api", "impact": "noise", "confidence": 0.45}
))

# ═══════════════════════════════════════════════
# DISCOVERY QUERIES (new competitors)
# ═══════════════════════════════════════════════
# 1. agentend — agents as backend
findings.append({
    "competitor": "new",
    "competitor_url": "https://agentend.ai",
    "query": "new backend-as-a-service 2026 agent MCP",
    "headline": "agentend — Agents as Backend: replace your entire backend with an agent",
    "url": "https://github.com/agentend/agentend",
    "announced_feature": "mcp-agent-api",
    "impact": "new-competitor",
    "librebase_delta": "New competitor candidate — agent-as-backend paradigm, evaluate whether to track",
    "raw_snippet": "agentend — The framework where the agent IS the backend. No routes, no controllers, no endpoint versioning. A user sends an intent, and the agent figures out the rest. GitHub stars: 1, created 2026-03-25.",
    "confidence": 0.50,
    "disposition": "uncertain",
})

# 2. Agent Stack (Linux Foundation/BeeAI)
findings.append({
    "competitor": "new",
    "competitor_url": "https://agentstack.beeai.dev",
    "query": "new open source BaaS 2026 agent",
    "headline": "Agent Stack — Open infrastructure for turning AI agents into running services (Linux Foundation)",
    "url": "https://github.com/i-am-bee/agentstack",
    "announced_feature": "mcp-agent-api",
    "impact": "new-competitor",
    "librebase_delta": "New competitor candidate — Linux Foundation project, MCP + A2A protocol, 1154 stars",
    "raw_snippet": "Agent Stack: open infrastructure for turning AI agents into running services. 15+ LLM providers, vector storage, auth, file handling, deployment tooling. MCP protocol integrations with OAuth. Helm chart for Kubernetes. 1154 GitHub stars, Apache 2.0.",
    "confidence": 0.55,
    "disposition": "uncertain",
})

# 3. Agent-Native
findings.append({
    "competitor": "new",
    "competitor_url": "https://agent-native.com",
    "query": "new developer platform 2026 AI agent backend",
    "headline": "Agent-Native — Open-source framework for agentic applications you own",
    "url": "https://github.com/yasku/agent-native",
    "announced_feature": "mcp-agent-api",
    "impact": "new-competitor",
    "librebase_delta": "New competitor candidate — actions + agent runtime + SQL-backed state, BYO database/hosting",
    "raw_snippet": "Agent-Native: open-source framework for agentic apps. Primitives: shared actions, SQL-backed state, identity, tools, skills, jobs, observability, UI surfaces. Actions callable from UI, agent, API, MCP, A2A, CLI. Backend agnostic — bring your own DB, hosting, model stack.",
    "confidence": 0.50,
    "disposition": "uncertain",
})

# 4. Supabase vs Firebase comparison (discovery context)
findings.append({
    "competitor": "new",
    "competitor_url": "https://supabase.com/alternatives/supabase-vs-firebase",
    "query": "alternative to supabase 2026 agent",
    "headline": "Supabase vs Firebase — Supabase positions as open-source Firebase alternative",
    "url": "https://supabase.com/alternatives/supabase-vs-firebase",
    "announced_feature": "postgresql-db",
    "impact": "new-competitor",
    "librebase_delta": "Supabase's open-source positioning vs Firebase is a competitive message to watch",
    "raw_snippet": "Supabase vs Firebase comparison page: Supabase is open-source backend on Postgres with auth, storage, realtime, functions. Self-hostable via Docker/Kubernetes/Terraform. Firebase is Google's NoSQL-based platform. Supabase highlights SQL predictability, RLS, self-host freedom.",
    "confidence": 0.45,
    "disposition": "not-a-competitor",
})

# 5. self-hosted AI agent landscape
findings.append({
    "competitor": "new",
    "competitor_url": "https://kiebot.com/insights/self-hosted-ai-agent-landscape-2026",
    "query": "self-host backend platform 2026 agent",
    "headline": "The 2026 Self-Hosted AI Agent Landscape: 16 Products Honestly Compared",
    "url": "https://kiebot.com/insights/self-hosted-ai-agent-landscape-2026",
    "announced_feature": "mcp-agent-api",
    "impact": "new-competitor",
    "librebase_delta": "Market context: self-hosted agent platforms are a growing category — OpenClaw (379k stars), Hermes Agent (199k), n8n (193k), Dify (146k)",
    "raw_snippet": "2026 self-hosted AI agent landscape: OpenClaw (379k+ stars, 22 channels, OpenAI/NVIDIA/GitHub sponsored), Hermes Agent (199k, self-improving learning loop), n8n (193k, visual workflow + AI nodes), Dify (146k, RAG+agent+workflow), Open WebUI (142k), AnythingLLM (62k), Flowise (54k), LibreChat (40k).",
    "confidence": 0.45,
    "disposition": "uncertain",
})

# ── Persist ──
print(f"Preparing {len(findings)} findings...", file=sys.stderr)
p = subprocess.run(
    [PYTHON, SCAN_CLI],
    input=json.dumps(findings),
    capture_output=True, text=True, cwd=DB_DIR
)
if p.returncode != 0:
    print(f"ERROR persisting (rc={p.returncode}): {p.stderr}", file=sys.stderr)
    sys.exit(1)
print(p.stdout.strip())

# ── Digest + Status ──
today_str = datetime.date.today().isoformat()
digest = subprocess.run(
    [PYTHON, SCAN_CLI, "--digest"],
    capture_output=True, text=True, cwd=DB_DIR
).stdout.strip()

status = subprocess.run(
    [PYTHON, SCAN_CLI, "--status"],
    capture_output=True, text=True, cwd=DB_DIR
).stdout.strip()

note = (
    "> **Automated daily scan** — Hermes cron at 09:00 CEST weekdays. "
    f"Scanned 13 known competitors + 6 discovery queries via web_search (keenable/exa backend). "
    "Confidence scores are coarse heuristics; treat as directional."
)

output = f"""
# LibreBase Competitive Intelligence — Daily Scan {today_str}

{note}

{digest}

---

## DB Status
{status}
"""

digest_path = os.path.join(DB_DIR, f"competitive_digest_{today_str}.md")
with open(digest_path, "w") as f:
    f.write(output.strip() + "\n")

print(f"\nDigest file: {digest_path}")
print()
print(output.strip())
