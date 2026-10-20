# LibreBase Competitive Intelligence — Daily Scan 2026-09-28

> **Automated daily scan** — Hermes cron at 09:00 CEST weekdays. Scanned 13 known competitors + discovery queries. Confidence scores are coarse heuristics; treat as directional.

---

## 🔴 Today's Headlines

### 1. Supabase open-sources "Evals" — AI agent benchmarking framework (August 1, 2026)

**Source:** [marktechpost.com](https://www.marktechpost.com/2026/08/01/supabase-releases-evals-an-open-source-benchmark-that-scores-claude-code-codex-and-opencode-on-real-supabase-tasks/) | [supabase.com/evals](https://supabase.com/evals) | [GitHub: supabase/evals](https://github.com/supabase/evals)

Supabase released **supabase/evals** under Apache-2.0 — a reproducible benchmark that runs AI coding agents (Claude Code, Codex, OpenCode) against real containerized Supabase stacks. Every scenario exercises the actual MCP server and CLI, not mocks. Scoring blends deterministic checks with LLM-as-a-judge; one retry allowed.

**Key results:**
- Opus 5 and Kimi K3 scored 100% on Build-stage tasks **unaided**
- Skills closed the gap for mid-tier: Sonnet 5 78%→100%, GPT-5.6 Sol 89%→100%, GPT-5.4 mini 78%→89%
- Three weaknesses surfaced: agents hand-write migrations instead of using declarative schemas; verify auth manually instead of using `@supabase/server`; docs usage varies sharply (Codex reads ~8 docs pages/scenario vs ~2 for Claude Code)

**Why this matters for LibreBase:**
Supabase is explicitly competing for the "AI agents building backends" positioning. The eval framework tests agent-driven backend work — exactly what LibreBase targets. Supabase's public leaderboard at `supabase.com/evals` creates a moat: developers optimizing for Supabase eval scores are developers locked into Supabase conventions. This validates LibreBase's MCP-agent-api thesis and raises the bar — competitors are now measuring agent fidelity, not just API coverage.

---

### 2. Supabase MCP server — enterprise auth via Okta (August 24, 2026)

**Source:** [supabase.com/blog](https://supabase.com/blog)

Enterprise IT admins can now manage access to Supabase in Claude centrally through Okta, scoped to each person's existing permissions. This is the MCP server graduating to enterprise-grade — signaling Supabase treats it as a core product.

---

### 3. Appwrite — hosted remote MCP server with OAuth (July 2026)

**Source:** [appwrite.io/blog](https://appwrite.io/blog/post/july-product-update-remote-mcp-server-projects-api-and-more)

Appwrite shipped a **hosted remote MCP server** at `mcp.appwrite.io` with OAuth authentication — no local install, no API keys to manage. Works with Claude Code, Cursor, Codex, VS Code, Windsurf, Zed. Also shipped Projects API and OAuth Device Authorization for CLI.

Appwrite is matching Supabase's MCP move. The competitive pressure on "which backend has the best MCP server" is now a three-way race (Supabase, Appwrite, Firebase).

---

### 4. Directus — native MCP server + multimodal AI Assistant

**Source:** [directus.io](https://directus.com/) | [directus.io/blog](https://directus.io/blog/directus-11-16-release)

Directus has a **native MCP server** (out of beta, v11.12+) built into the platform. Their AI Assistant (v11.16) can now process images and PDFs across OpenAI, Anthropic, and Google Gemini. Deployment module added Vercel + Netlify support with role-based access and provider webhooks.

Directus is competing for "backend that AI agents connect to" from a CMS/headless angle — positioning as: "Connect any database. Get instant APIs, a no-code interface, and a native MCP server."

---

### 5. Firebase MCP server — GA + agent skills + Firestore Remote MCP

**Source:** [firebase.google.com](https://firebase.google.com/) | [codex.danielvaughan.com](https://codex.danielvaughan.com/2026/05/25/codex-cli-firebase-development-mcp-server-agent-skills-fullstack-workflows)

Firebase MCP server is GA (October 2025) with 50+ tools across 12 service categories, shipped inside `firebase-tools`. Agent skills catalogue landed early 2026. **Firestore Remote MCP reached GA April 23, 2026** — a hosted HTTP endpoint for Firestore-only access. Firebase has the widest MCP coverage of any backend platform.

---

### 6. 🔴 NEW COMPETITOR: Nubase — AI-native backend for coding agents

**Source:** [github.com/OtterMind/Nubase](https://github.com/OtterMind/Nubase) | [hysenlabs.com review](https://hysenlabs.com/en/projects/ottermind-nubase)

**OtterMind Nubase** is an open-source (Apache-2.0), self-hostable AI-native backend platform built specifically for AI coding agents. Java-based, single Docker image bundling Postgres + Redis + backend + Studio UI.

**Eight modules:** Database (PostgREST-compatible, per-project Postgres), Auth (Supabase-style), Storage (S3/R2-compatible), Assets (static CDN for generated frontends), Functions (edge functions), AI Gateway (OpenAI/Anthropic-compatible), **Memory** (Mem0-style with pgvector hybrid retrieval), Cron.

**Key differentiator:** Memory as a first-class primitive — durable memory, entity extraction, hybrid retrieval over pgvector + Postgres full-text + entity boost. Not bolted on as a separate vector store.

**Positioning vs Supabase:** "Supabase is excellent, but its open-source self-hosted stack is designed around a single project. Nubase is built for AI teams and self-hosters who want one Studio, one backend service, and many isolated AI projects."

**Nubase MCP:** `npx -y nubase_cli@latest install-skills` installs skills for Claude Code + Codex, wires up MCP config, opens browser for authorization. Agents can create tables, call REST APIs, write memory, inspect schema through MCP tools.

**Stats:** 627 GitHub stars, 74 forks, v0.1.4 (June 2026). Early stage but positioning is laser-targeted at LibreBase's space.

**Impact on LibreBase:** This is the most direct competitive threat found this scan. Nubase targets the exact same "AI agents building backends" wedge with MCP-first design, self-hostable Postgres backend, and a memory primitive LibreBase doesn't have. **LibreBase delta:** Evaluate adding a memory primitive to the roadmap; assess whether Nubase's multi-project isolation model is a differentiator we should match.

---

### 7. Heroku — Managed Inference and Agents GA with MCP support

**Source:** [heroku.com/blog](http://heroku.com/blog/managed-inference-and-agents-now-generally-available)

Heroku Managed Inference and Agents is GA. Uses MCP to give agents capabilities — currently STDIO MCP servers, with remote MCP servers (OAuth + buildpacks) in active development. Heroku is positioning as an AI-native PaaS, not a direct BaaS competitor but relevant for the "where do agents run" question.

---

### 8. PocketBase — active development, no agent story

**Source:** [github.com/pocketbase/pocketbase](https://github.com/pocketbase/pocketbase)

Daily commits, v0.22.x churn. Recent: Go 1.27.1 minimum, encoding/json/v2 upgrade, UI bumps. No MCP, no agent features, no blog. Still a single-file SQLite backend with no agent story — not a threat on the MCP-agent-api axis.

---

### 9. Render — new compute plans + Pro/Scale pricing

**Source:** [render.com/blog](https://render.com/blog/better-pricing-for-fast-growing-teams) | [render.com/changelog](https://render.com/changelog)

New Pro and Scale plans with no seat fees, more self-serve compliance features, fairer bandwidth billing. New compute plans with memory-optimized tiers and 12-CPU tier. Infrastructure play, not BaaS.

---

### 10. Other competitors — minimal movement

| Competitor | Status |
|---|---|
| Railway | No MCP/agent features detected; infrastructure play |
| Fly.io | No MCP/agent features detected; infra/platform |
| AWS Amplify | Node.js 24 support added May 2026; no agent/MCP moves |
| Koywe | Payment APIs for Latin America; not a BaaS competitor |

---

## Discovery: No New BaaS Entrants

Discovery queries (`new backend-as-a-service 2026 agent MCP`, `alternative to supabase 2026 agent`, `self-host backend platform 2026 agent`) returned no new BaaS competitors. The BaaS space is mature; the action is in MCP/agent features on existing platforms. The most notable discovery was **Nubase** surfacing via the `self-host backend platform 2026 agent` angle — it's not a traditional BaaS but an AI-native backend specifically for coding agents.

Additionally, Google unveiled **AX (Agentic Orchestrator)** on September 18, 2026 — open-source under Apache 2.0, a declarative API for composing autonomous AI agents across cloud/edge/device. Not a BaaS but relevant infrastructure for the agent ecosystem LibreBase operates in.

---

## DB Status

```
DB: /Users/julian/Documents/coding-projects/librebase/librebase_competitive.db
Competitors tracked: 34 (active: 34)
Today's scans: 14  (strong: 8, weak: 2)
Total scans logged: 503
Total feature-history changes: 59
Positioning features tracked: 24
```

---

## Competitive Positioning Summary

| Axis | Leader | LibreBase Position |
|---|---|---|
| **MCP server quality** | Firebase (50+ tools, GA, remote MCP) | Needs MCP server — core gap |
| **MCP + enterprise auth** | Supabase (Okta integration) | Not applicable (self-hosted focus) |
| **Agent benchmarking** | Supabase (Evals, public leaderboard) | No agent eval framework — opportunity |
| **AI-native backend (agent-first)** | Nubase (MCP-first, memory primitive) | Direct competitor — watch closely |
| **Self-hostable BaaS** | Supabase (mature OSS), PocketBase (simple) | LibreBase's niche if positioned well |
| **Multi-project isolation** | Nubase (per-project DBs, one Studio) | Supabase self-hosted = single project |
| **Memory as backend primitive** | Nubase (built-in, pgvector) | Not yet — potential differentiator |
| **CMS + MCP** | Directus (native MCP, multimodal AI) | Adjacent competitor from CMS side |

---

*Digest generated: 2026-09-28 09:00 CEST*
