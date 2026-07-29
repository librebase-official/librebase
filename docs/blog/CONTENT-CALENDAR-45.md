# Librebase blog calendar — 45 posts (questions, topics, keywords)

Majico staging project `af1f6d03-4b45-4cb5-8276-548cfacd71ee`.  
`suggest_blog_opportunities` returned empty until niche research completes; this calendar is the GTM seed. Prefer Majico `run_blog_research` → outline → draft → publish once workers are green.

Pillars: **Q** question / **T** topic / **K** keyword cluster.

| # | Pillar | Working title | Primary keyword | Intent |
|---|--------|---------------|-----------------|--------|
| 1 | Q | What is a Postgres-compatible database? | postgres compatible database | informational |
| 2 | Q | What does “written in Li” mean for a database? | li language database | informational |
| 3 | Q | Why do AI agents need their own database stack? | database for ai agents | informational |
| 4 | Q | What is an agentic database? | agentic database | informational |
| 5 | Q | How is Librebase different from Supabase? | supabase alternative | commercial |
| 6 | Q | Can you self-host a Supabase-like stack? | self hosted postgres platform | commercial |
| 7 | Q | What is row-level security in Postgres? | row level security postgres | informational |
| 8 | Q | Why does database memory footprint matter for agents? | low memory database | informational |
| 9 | Q | What is MCP and why does a database expose it? | mcp database | informational |
| 10 | Q | Auth + REST + Realtime — what do you actually need? | auth rest realtime database | informational |
| 11 | T | Postgres for short-lived agent sessions | agent sessions postgres | informational |
| 12 | T | Honest health status vs fake-green dashboards | database health monitoring | informational |
| 13 | T | Dedicated vs shared database instances | dedicated database instance | informational |
| 14 | T | REST `/rest/v1` for agent clients | postgrest style api | informational |
| 15 | T | Shipping RLS before Storage and Edge | rls before storage | informational |
| 16 | T | Studio SQL console for platform teams | database studio sql | informational |
| 17 | T | Capability matrices that stay incomplete | open source roadmap honesty | brand |
| 18 | T | Low-footprint databases on dense hosts | dense hosting database | informational |
| 19 | T | Native compile vs GC runtimes for data planes | native database runtime | informational |
| 20 | T | Agent MCP tools for projects and health | mcp tools database | informational |
| 21 | K | Best Supabase alternatives for self-hosting (2026) | supabase alternative self host | commercial |
| 22 | K | Postgres Auth patterns for multi-tenant agents | multi tenant postgres auth | informational |
| 23 | K | Realtime for agent workflows without overkill | postgres realtime agents | informational |
| 24 | K | Open-source Postgres platforms compared | open source postgres platform | commercial |
| 25 | K | Database for Cursor / Claude agent stacks | database for cursor agents | commercial |
| 26 | K | Edge-adjacent Postgres: when small footprint wins | edge postgres footprint | informational |
| 27 | K | Service role vs anon keys explained | supabase service role key | informational |
| 28 | K | Waitlists and early access for infra products | saas waitlist best practices | brand |
| 29 | K | Formal contracts vs marketing parity claims | api contract testing | informational |
| 30 | K | Li language for systems infra | li programming language | informational |
| 31 | Q | Is Librebase production-ready? | librebase production ready | commercial |
| 32 | Q | How do I connect with the Postgres wire protocol? | postgres wire protocol | informational |
| 33 | Q | Do agents need RLS? | row level security agents | informational |
| 34 | Q | What breaks when Auth is bolted on later? | database auth by design | informational |
| 35 | Q | Shared runtime vs one container per project? | multi project database runtime | informational |
| 36 | T | Migrating a toy Supabase app to Librebase | migrate from supabase | commercial |
| 37 | T | Measuring REST and Auth before you claim parity | rest auth parity tests | informational |
| 38 | T | Designing schemas for autonomous writers | agent write schemas | informational |
| 39 | T | Observability for agent-driven write storms | agent write storm | informational |
| 40 | T | Cost of memory on cloud VMs for data APIs | database memory cost | commercial |
| 41 | K | “Postgres for agents” search intent map | postgres for agents | commercial |
| 42 | K | MCP server patterns for data products | mcp server database | informational |
| 43 | K | Honest degraded modes in developer platforms | degraded mode status | brand |
| 44 | K | Local-first database workflows for agents | local first database agents | informational |
| 45 | K | Librebase waitlist: what early access includes | librebase waitlist | brand |

## Drafts in repo

See `docs/blog/drafts/` for seed articles (1–5). Expand via Majico when `run_blog_research` is available.

## Publish path (Majico)

1. `suggest_blog_opportunities` (after niche job completes)  
2. `run_blog_research` with concept  
3. `generate_blog_outline` → user approve  
4. `generate_blog_section` / `assemble_blog_post`  
5. `publish_blog_post`
