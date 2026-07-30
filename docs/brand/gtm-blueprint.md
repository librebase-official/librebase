# GTM blueprint

**Product:** Librebase  
**Project ID:** af1f6d03-4b45-4cb5-8276-548cfacd71ee  
**Source:** Majico staging niche research `071be8dd-45ff-4937-a735-898805e4a58c` + brand profile (sage / outlaw)  
**Note:** Studio `gtm_strategy` pipeline was enqueued 2026-07-30 but workers timed out / left harness pending; this blueprint is synthesized from the completed GTM direction suggestion so agents have a usable handoff.

**Target market:** Security-conscious agent teams and platform engineers in regulated industries who need a Postgres-compatible backend without vendor lock-in or obscured cost structures.

**Positioning:** Agent-first data layer that replaces the fake-green SaaS dashboard with raw, transparent health metrics — high-performance Postgres-compatible database written in Li, low memory, strong security defaults, Auth/REST/Realtime and native MCP.

**Primary channel:** Developer forums (e.g. r/Postgres) and MCP protocol community Discord

**Supporting channels:** Hacker News, GitHub Discussions / README SEO, technical Twitter/X threads, comparison posts vs Supabase / Neon / Turso

**Content engine focus:** Honest health metrics, memory footprint, MCP integration, Li-native runtime, vendor lock-in avoidance, regulated-industry transparency

**Primary message:**

Open Backend for Agent Workflows. Low memory. Strong security defaults. Auth, REST, and Realtime for teams and agents — with health status you can trust, not fake-green SaaS dashboards.

## Jobs-to-be-Done canvas

**Job performer:** Platform engineer or agent-builder evaluating a Postgres-compatible backend for autonomous agents and regulated workloads.

**Focus job:** Stand up a small-footprint, transparent data layer agents can talk to via MCP/REST without inheriting managed-BaaS lock-in or opaque billing.

**Job stories:**
- When I am wiring agents to a database, I want to use open protocols (MCP/REST) so I can swap runtimes without rewriting proprietary client SDKs.
- When I am budgeting infra for regulated work, I want honest health and memory metrics so I can calculate real operating cost instead of trusting a green dashboard.
- When I am comparing Supabase-shaped stacks, I want a lean Postgres-compatible option so I can keep Auth/REST/Realtime without a heavy managed overhead.

**Success criteria:**
- Agents connect via MCP/REST without proprietary lock-in
- Steady-state footprint stays lean (target: dedicated lean profile; engineering gate documented honestly)
- Health surfaces report real status (no fake-green)
- Clear differentiation from LibreOffice Base (desktop DB) in search and docs

**Circumstances:**
- Building agent workflows that need a real data plane
- Evaluating open alternatives to managed BaaS
- Operating under compliance or cost transparency pressure

**Aspirations:**
- Own infrastructure and cost visibility end-to-end
- Ship agent-first products on a small, secure Postgres-compatible core
- Avoid vendor lock-in from proprietary client libraries

## Competitive wedge

| Competitor | Librebase counter |
|------------|-------------------|
| Supabase | Same shape (Auth/REST/Realtime) without heavy resource use and hidden Pro-tier cost opacity |
| Neon | Serverless branching without native agent/MCP-first APIs |
| Turso | Edge-light footprint plus fuller Auth/REST/Realtime + MCP story |

**Whitespace:** The gap between lightweight edge databases lacking native Auth/REST APIs and heavy managed backends that hide costs.

**Motion:** Product-led waitlist — zero-cost evaluation for enterprise-grade security defaults without hidden fees.

## Name conflict

Differentiate from **LibreOffice Base**. Emphasize agent-first backend + MCP, not a desktop spreadsheet database. Preferred qualifier tagline: **Open Backend for Agent Workflows**.

## Agent usage

1. Read this file with [ICP-GTM.md](./ICP-GTM.md) and [BRAND.md](./BRAND.md).
2. Landing / waitlist copy: lead with honesty + footprint + MCP — not “AI-powered” fluff.
3. Channels: ship technical proof (benches, health UX, MCP demos) to the primary community channels above.
4. When Majico Studio `gtm_strategy` completes, replace this file with the official `gtm-blueprint.md` export from `/gtm-blueprint/assets`.
