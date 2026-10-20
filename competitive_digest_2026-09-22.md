# LibreBase Competitive Intelligence — Daily Scan 2026-09-22

> **Automated daily scan** — Hermes cron at 09:00 CEST weekdays. Scanned 13 known competitors + discovery queries. Confidence scores are coarse heuristics; treat as directional.

## 🚨 STRONG SIGNAL ALERTS

13 strong signals across 9 competitors. The dominant theme: **every major BaaS competitor is shipping agent/MCP features, and LibreBase is weak on mcp-agent-api.**

### Supabase — The Supabase MCP Server (2.7K stars, OAuth 2.1, 8 tool groups)
- Feature: `mcp-agent-api` | Impact: 🔴 strong | Confidence: 65%
- [chatforest.com/reviews/supabase-mcp-server](https://chatforest.com/reviews/supabase-mcp-server)

### Supabase — Introducing Supabase Evals (Claude Code 91%, OpenCode 78%, open-source benchmark)
- Feature: `mcp-agent-api` | Impact: 🔴 strong | Confidence: 65%
- [supabase.com/blog/supabase-evals](https://supabase.com/blog/supabase-evals)

### Appwrite — MCP Server 2.0 (two-tool architecture, all services by default)
- Feature: `mcp-agent-api` | Impact: 🔴 strong | Confidence: 65%
- [appwrite.io/blog/post/announcing-appwrite-mcp-server-2](https://appwrite.io/blog/post/announcing-appwrite-mcp-server-2)

### Firebase — Eval-driven agent skills (pass rate 31.7% → 78.0% with skills)
- Feature: `mcp-agent-api` | Impact: 🔴 strong | Confidence: 65%
- [firebase.blog/posts/2026/08/eval-driven-development-agent-skills/](https://firebase.blog/posts/2026/08/eval-driven-development-agent-skills/)

### PocketBase — Community MCP servers (tokenscompany, Mabel Data, jeremielondon)
- Feature: `mcp-agent-api` | Impact: 🔴 strong | Confidence: 65%
- [mcpservers.org/servers/tokenscompany/pocketbase-mcp](https://mcpservers.org/servers/tokenscompany/pocketbase-mcp)

### Nhost — Turn any project into an agentic service (MCP + embedded docs CLI)
- Feature: `mcp-agent-api` | Impact: 🔴 strong | Confidence: 65%
- [nhost.io/blog/newsletter-2026q1](https://nhost.io/blog/newsletter-2026q1)

### Directus v12.3 — Search-first MCP tool discovery + OAuth 2.1
- Feature: `mcp-agent-api` | Impact: 🔴 strong | Confidence: 65%
- [directus.com/resources/12.3-release-notes](https://directus.com/resources/12.3-release-notes)

### Directus v11.16 — Multimodal AI (images + PDFs, OpenAI/Anthropic/Gemini)
- Feature: `vector-embeddings` | Impact: 🔴 strong | Confidence: 65%
- [directus.com/resources/directus-11-16-release](https://directus.com/resources/directus-11-16-release)

### Xano — Xano Agent replaces Logic Assistant, MCP-first infrastructure
- Feature: `mcp-agent-api` | Impact: 🔴 strong | Confidence: 65%
- [docs.xano.com/updates](https://docs.xano.com/updates)

### Railway — Railway Agent + Remote MCP (Claude Code, Codex, OpenCode, Pi harnesses)
- Feature: `mcp-agent-api` | Impact: 🔴 strong | Confidence: 65%
- [railway.app/changelog](https://railway.app/changelog)

### Render — 12-CPU/96GB plans for agent platforms, "deploy and scale any app or agent"
- Feature: `mcp-agent-api` | Impact: 🔴 strong | Confidence: 65%
- [render.com/changelog/new-compute-plans-and-new-ids-for-existing-plans](https://render.com/changelog/new-compute-plans-and-new-ids-for-existing-plans)

### Fly.io — "Where agents like to run" — Sprites with Connectors
- Feature: `mcp-agent-api` | Impact: 🔴 strong | Confidence: 65%
- [fly.io/blog/kurt-scott-money-sprites/](https://fly.io/blog/kurt-scott-money-sprites/)

### AWS Amplify — AI features: Interactions, Predictions, GenAI via Bedrock
- Feature: `vector-embeddings` | Impact: 🔴 strong | Confidence: 65%
- [aws.amazon.com/amplify/features](https://aws.amazon.com/amplify/features)

## 🆕 NEW COMPETITOR CANDIDATES (3)

1. **Back4app** — Built-in AI Agent + MCP support for Cursor/Windsurf. [back4app.com](https://www.back4app.com/backend-as-a-service-baas)
2. **InsForge** — "Supabase for AI agents" — MCP-first BaaS, YC-backed, alpha Mar 2026. [dev.to/danieltechlab/insforge...](https://dev.to/danieltechlab/insforge-rebuilt-the-baas-stack-so-ai-agents-not-humans-are-the-primary-operator-34im)
3. **Rayfin** — Open-source BaaS (MIT) on Microsoft Fabric. Decorator-driven TypeScript, first-class agent plugins. [wenfeng.my/microsoft-fabric-apps-rayfin...](https://wenfeng.my/microsoft-fabric-apps-rayfin-open-source-baas)

## 📊 DB STATUS

- Competitors tracked: 34 (active: 34)
- Today's scans: 54 (strong: 13, weak: 0, new-competitor: 3, noise: 27)
- Total scans logged: 420
- Total feature-history changes: 58
- Positioning features tracked: 24

## 🎯 KEY TAKEAWAY

The competitive landscape has shifted decisively. **13 of 54 findings (24%) are strong signals**, and the overwhelming majority are about agent/MCP capabilities. Every major competitor now has:
- An official or community MCP server (Supabase, Appwrite, Firebase, Directus, Nhost, Railway, PocketBase community)
- Agent-specific product positioning (Railway, Render, Fly.io, Xano)
- Eval/benchmark frameworks for agent performance (Supabase Evals, Firebase eval-driven skills)

LibreBase's `mcp-agent-api` feature is the clear attack surface. Competitors are not just adding MCP — they're building eval frameworks, agent-specific pricing, and agent-native infrastructure primitives around it.
