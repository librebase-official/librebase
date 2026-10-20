#!/usr/bin/env python3
"""
Merge librebase_competitive.db (market research DB — canonical) with
my competitor_research.db additions: missing competitors + trend_tags.

Market research DB schema (canonical):
  competitors, our_positioning (24 features), competitor_features (312 rows),
  daily_scans (36 today), competitor_feature_history (12), discovery_log (3)

My additions to merge:
  - 15 new competitors (convex, vercel, cloudflare-workers, retool, baseten,
    langchain, openai-agents, anthropic, elevenlabs, huggingface, nango,
    merge-dev, sequin, neon, electricsql)
  - 24 trend_tags (for taxonomy/analysis)
  - Backfill: azure-static-webapps, lora, powerdns (watch list)

Run: python3 merge_competitive_db.py
"""

import os
import sqlite3
from datetime import date

CANDIDATE_DB = os.path.expanduser(
    "~/Documents/coding-projects/librebase/librebase_competitive.db"
)
MY_DB = os.path.expanduser(
    "~/Documents/coding-projects/librebase/data/marketing/competitor_research.db"
)

NEW_COMPETITORS = [
    # (name, url, category, notes)
    ("Convex", "https://convex.dev", "BaaS",
     "Hosted backend platform — deterministic distributed DB, real-time queries, serverless functions. TypeScript-native. No agent/MCP story observed."),
    ("Vercel", "https://vercel.com", "Cloud",
     "Frontend/cloud platform — serverless functions, edge middleware, storage (Vercel KV/Postgres/Blob). Moving into backend territory. Watch for BaaS expansion."),
    ("Cloudflare Workers", "https://developers.cloudflare.com", "Cloud",
     "Edge compute + managed services (KV, D1, R2, Durable Objects). Full backend capabilities at the edge. Not traditional BaaS but competes for backend-build budget."),
    ("Retool", "https://retool.com", "BaaS",
     "Low-code internal tooling — connects to any DB/API. Expanding into AI-assisted app building. Overlaps on 'build on top of your data' angle."),
    ("Baseten", "https://baseten.com", "AI-platform",
     "Model deployment platform for ML/AI — serves models at scale. Competing in the AI-backend space. No BaaS overlaps directly but relevant for AI-feature benchmarking."),
    ("LangChain", "https://python.langchain.com", "AI-platform",
     "Framework for building LLM-powered apps. Moving from library to platform with LangChain Cloud / deployments. Relevant for agent-framework benchmarking."),
    ("OpenAI Agents", "https://platform.openai.com", "AI-platform",
     "OpenAI's agent SDK + assistants API + function calling. The reference point for AI backend features. Agent SDK (2024+) + structured outputs."),
    ("Anthropic", "https://anthropic.com", "AI-platform",
     "Claude API + computer use + agentic capabilities. Competing with OpenAI on agentic/cloud backend features. Claude Agent SDK."),
    ("ElevenLabs", "https://elevenlabs.io", "AI-platform",
     "Voice AI platform — TTS, voice cloning, agent orchestration. Expanding into agentic voice backend."),
    ("HuggingFace", "https://huggingface.co", "AI-platform",
     "Model hub + inference endpoints + Spaces. The open-source AI platform — increasingly a backend for AI features. Inference API, Spaces, AutoTrain."),
    ("Nango", "https://getsoku.com", "BaaS",
     "Integration platform — sync data between SaaS APIs. Adjacent to BaaS for data integration use cases. Open-source integration platform."),
    ("Merge.dev", "https://merge.dev", "BaaS",
     "Unified API for SaaS integrations — abstracts hundreds of integrations into one API. Competing for data-integration BaaS use cases."),
    ("Sequin", "https://sequin.io", "Backend",
     "Stream Postgres changes to upstream destinations. Adjacent to BaaS realtime/CDC use cases. Postgres-to-Kafka/SQS/etc. sync."),
    ("Neon", "https://neon.tech", "BaaS",
     "Serverless Postgres — auto-scaling, branching, separate storage/compute. Direct competitor for Postgres-backed BaaS features (DB + branching as a feature)."),
    ("ElectricSQL", "https://electric-sql.com", "Backend",
     "Local-first sync layer — sync Postgres to local SQLite/WASM. Competing on the edge-local-backend axis. Local-first architecture."),
    # Watch list
    ("Azure Static Web Apps", "https://azure.microsoft.com/en-us/services/app-service/static/", "BaaS",
     "Azure's static web apps with integrated API (Cosmos DB, Functions), auth, and GitHub integration. Enterprise player — watch for expansion."),
    ("LoRA", "https://lora.company", "AI-platform",
     "Open-source LoRA training + inference platform. Edge cases for AI model serving. Watch for integration with BaaS platforms."),
    ("PowerDNS", None, "Other",
     "DNS + infrastructure — not BaaS but relevant if librebase expands into DNS/domain management. Tracked as adjacent infra."),
]

TREND_TAGS = [
    ("ai-agents", "ai", "AI agent frameworks, agentic APIs, agent-first design"),
    ("agentic-ux", "ai", "Agentic UX patterns, tool-use, function calling"),
    ("llm-saas", "ai", "LLM-powered SaaS products and features"),
    ("ai-cloud-infra", "ai", "Cloud infrastructure for AI workloads"),
    ("serverless", "cloud", "Serverless compute, edge functions, cold-start-free"),
    ("edge-compute", "cloud", "Edge computing, distributed cloud"),
    ("kubernetes", "cloud", "K8s ecosystem, managed K8s, serverless K8s"),
    ("postgres", "backend", "PostgreSQL ecosystem, extensions, managed Postgres"),
    ("realtime", "backend", "Real-time APIs, websockets, live data sync"),
    ("auth", "backend", "Authentication, auth providers, SSO, identity"),
    ("open-source-baas", "baas", "Open-source backend-as-a-service alternatives"),
    ("supabase-alternatives", "baas", "Competitors and alternatives to Supabase"),
    ("pricing-changes", "market", "Competitor pricing changes, new plans, discounts"),
    ("funding", "market", "Funding rounds, acquisitions, partnerships"),
    ("hiring", "market", "Hiring signals — team growth, new roles"),
    ("developer-adoption", "market", "Developer community growth, GitHub stars, SDK releases"),
    ("feature-launch", "devtools", "New feature or product launches"),
    ("api-changes", "devtools", "API deprecations, new endpoints, breaking changes"),
    ("sdk-release", "devtools", "New SDKs, CLI tools, client libraries"),
    ("documentation", "devtools", "Documentation updates, new guides, tutorials"),
    ("enterprise-features", "devtools", "Enterprise features: SSO, RBAC, audit logs, SLAs"),
    ("go-to-market", "market", "New positioning, repositioning, messaging shifts"),
    ("ai-competitor-wave", "ai", "The broader wave of competitors adding AI/agent/MCP features"),
    ("self-host-k8s", "baas", "Self-host + Kubernetes as a BaaS differentiator"),
]


def merge():
    cand = sqlite3.connect(CANDIDATE_DB)
    cand.row_factory = sqlite3.Row
    cand.execute("PRAGMA journal_mode=WAL")
    cand.execute("PRAGMA foreign_keys=ON")

    my = sqlite3.connect(MY_DB)
    my.row_factory = sqlite3.Row

    today = date.today().isoformat()

    # ── 1. Add missing competitors ────────────────────────────────────────────
    existing = {r["name"].lower(): r["id"] for r in cand.execute("SELECT name, id FROM competitors")}
    added = 0
    for name, url, category, notes in NEW_COMPETITORS:
        if name.lower() in existing:
            print(f"  ✓ {name} — already exists")
            continue
        cand.execute(
            """INSERT INTO competitors (name, url, category, first_seen, active, notes)
               VALUES (?, ?, ?, ?, 1, ?)""",
            (name, url, category, today, notes),
        )
        added += 1
        print(f"  + {name} — added ({category})")

    print(f"\n  Competitor additions: {added}")

    # ── 2. Add trend_tags table + data ────────────────────────────────────────
    tags_existing = cand.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='trend_tags'"
    ).fetchone()
    if not tags_existing:
        cand.execute(
            """CREATE TABLE trend_tags (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               name TEXT NOT NULL UNIQUE,
               category TEXT NOT NULL,
               description TEXT
            )"""
        )
        print("  ✓ trend_tags table created")
    else:
        print("  ✓ trend_tags table already exists")

    # Seed tags
    existing_tags = {r["name"] for r in cand.execute("SELECT name FROM trend_tags")}
    tag_added = 0
    for name, category, description in TREND_TAGS:
        if name in existing_tags:
            continue
        cand.execute(
            "INSERT INTO trend_tags (name, category, description) VALUES (?, ?, ?)",
            (name, category, description),
        )
        tag_added += 1
        print(f"  + tag: {name} ({category})")

    print(f"\n  Trend tag additions: {tag_added}")

    # ── 3. Add finding_tags join table ────────────────────────────────────────
    join_existing = cand.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='finding_tags'"
    ).fetchone()
    if not join_existing:
        cand.execute(
            """CREATE TABLE finding_tags (
               finding_id INTEGER NOT NULL,
               tag_id INTEGER NOT NULL,
               PRIMARY KEY (finding_id, tag_id),
               FOREIGN KEY (finding_id) REFERENCES daily_scans(id) ON DELETE CASCADE,
               FOREIGN KEY (tag_id) REFERENCES trend_tags(id) ON DELETE CASCADE
            )"""
        )
        print("  ✓ finding_tags join table created")
    else:
        print("  ✓ finding_tags join table already exists")

    # ── 4. Add new_competitor_discovery table (for discovered competitors) ────
    disc_existing = cand.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='new_competitor_discovery'"
    ).fetchone()
    if not disc_existing:
        # discovery_log already exists — add a notes column for disposition detail
        cand.execute("ALTER TABLE discovery_log ADD COLUMN category TEXT DEFAULT ''")
        print("  ✓ discovery_log.category column added")
    else:
        print("  ✓ new_competitor_discovery already exists")

    cand.commit()
    cand.close()
    my.close()

    print(f"\n✅ Merge complete. DB: {CANDIDATE_DB}")
    print(f"   Competitors now: {len(existing) + added}")
    print(f"   Trend tags now: {len(existing_tags) + tag_added}")

    # Verify
    verify = sqlite3.connect(CANDIDATE_DB)
    verify.row_factory = sqlite3.Row
    total_comp = verify.execute("SELECT COUNT(*) FROM competitors").fetchone()[0]
    active = verify.execute("SELECT COUNT(*) FROM competitors WHERE active=1").fetchone()[0]
    total_tags = verify.execute("SELECT COUNT(*) FROM trend_tags").fetchone()[0]
    scans_today = verify.execute(
        "SELECT COUNT(*) FROM daily_scans WHERE date(scanned_at) = ?", (today,)
    ).fetchone()[0]
    print(f"\n   Verification:")
    print(f"   Competitors: {total_comp} (active: {active})")
    print(f"   Trend tags: {total_tags}")
    print(f"   Today's scans: {scans_today}")
    verify.close()


if __name__ == "__main__":
    merge()
