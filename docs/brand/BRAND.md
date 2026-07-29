# Librebase — Brand Guidelines (Agent Handoff)

**Project ID:** af1f6d03-4b45-4cb5-8276-548cfacd71ee  
**Source:** Majico staging (brief refreshed 2026-07-29)  
**Companion:** [DESIGN.md](./DESIGN.md)

---

## 1. Identity

- **Name:** Librebase
- **One-liner:** A PostgreSQL platform that stays small and honest.
- **Support line:** Aiming for about 64 MB of RAM with speed in the same class as managed Postgres stacks, strong sign-in defaults, usual database connection plus web interfaces and live updates for teams and AI tools.
- **Audience:** Developers, platform teams, and people building with AI assistants who need a PostgreSQL-compatible backend with a small footprint and honest health status.
- **Primary CTA:** Join the waitlist for early access
- **Secondary CTA:** Open the console
- **Copy rule:** Prefer plain words over jargon and abbreviations on marketing pages (say PostgreSQL, sign-in, web interfaces, per-row access rules; explain Li once).
- **Metrics rule:** Frame **64 MB** and **Supabase-class speed** as **aims / targets** until CI benches publish green rows ([lidb footprint](https://github.com/li-langverse/lidb/blob/main/docs/footprint.md)). Never state them as measured facts without evidence.

### Niche keywords

postgres compatible database, agentic database, low memory database, supabase alternative, mcp database, li language database, row level security postgres, self hosted postgres platform, auth rest realtime database, database for ai agents

---

## 2. Voice

- Direct, technical, short.
- Lead with outcome, then mechanism.
- Honest status — no fake-green parity claims.
- Avoid: “AI-powered”, “deserve”, “built for what matters”, consultant jargon, unverifiable metrics.

---

## 3. Messaging anchors

| Surface | Copy |
|--------|------|
| Hero | A PostgreSQL platform that stays small and honest. |
| Problem | Apps and AI tools need a database that keeps up. |
| Proof | Written in Li; aiming for ~64 MB RAM and Supabase-class speed on the core path (bench-gated); console shows real health. |
| Final CTA | Join the waitlist for early access |

---

## 4. Visual (interim)

- Landing typography: **Orbitron** (hero + wordmark only) + **Space Grotesk** (body / section titles) + IBM Plex Mono. Do not use the display face on every heading.
- Majico curated pair id: `orbitron-space`. Palette/logo not finalized (`hasBrandData` false until niche workers complete + palette/logo select).
- Do not replace live landing fonts with `system-ui` from scaffold export until palette is chosen.

---

## 5. Product truth

- Core path first: queries, web interfaces, sign-in, per-row access rules.
- Status list stays incomplete until tests pass.
- Self-host + cloud waitlist.
- Assistant tools for AI; web console for people.

---

## 6. Do / don’t

| Do | Don’t |
|----|--------|
| Speak to builders and people using AI tools | Address “everyone” |
| Name Li once, then say PostgreSQL and plain outcomes | Invent logos, quotes, or user counts |
| Link the status list for honest progress | Claim full Supabase parity |
| Keep CTAs: waitlist + console | Vague “Learn more” as primary |
| Prefer plain words on marketing pages | Unexplained abbreviations (Auth, REST, RLS, MCP, FAQ) |
| Say “aiming for ~64 MB” / “target speed class” | Claim measured 64 MB or “as fast as Supabase” without published benches |

---

## 7. Majico pipeline status

- Brief submitted with new pitch (`briefId` 713bac42…).
- Niche research / logo / landing-page / guideline-html jobs were **pending** on workers as of export.
- Re-poll `list_project_assets` / `suggest_blog_opportunities` after workers drain; then `list_palette_options` → `select_palette`, `list_logo_candidates` → `select_logo`, `download_export_zip` again.
