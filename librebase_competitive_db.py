#!/usr/bin/env python3
"""
LibreBase Competitive Intelligence Database
=====================================
Idempotent init + seed. Run once (safe to re-run).

DB path: LIBREBASE_COMPETITIVE_DB env var, default ~/librebase_competitive.db
"""

import sqlite3
import os
import sys
from datetime import date, datetime, timezone

DB_PATH = os.environ.get(
    "LIBREBASE_COMPETITIVE_DB",
    os.path.expanduser("~/Documents/coding-projects/librebase/librebase_competitive.db"),
)

# ── Schema ──────────────────────────────────────────────────────────────

SCHEMA = """
-- Competitors we track
CREATE TABLE IF NOT EXISTS competitors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    url TEXT,
    category TEXT,
    first_seen TEXT NOT NULL DEFAULT (date('now')),
    active INTEGER DEFAULT 1,
    notes TEXT
);

-- Our own positioning matrix (static, curated; updated manually when we change)
CREATE TABLE IF NOT EXISTS our_positioning (
    feature TEXT PRIMARY KEY,
    our_offer TEXT NOT NULL,
    strength TEXT NOT NULL CHECK(strength IN ('strong','neutral','weak')),
    notes TEXT,
    updated_at TEXT NOT NULL DEFAULT (date('now'))
);

-- Competitor capability matrix (per-feature assessment)
CREATE TABLE IF NOT EXISTS competitor_features (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    competitor_id INTEGER NOT NULL REFERENCES competitors(id) ON DELETE CASCADE,
    feature TEXT NOT NULL,
    offered INTEGER NOT NULL DEFAULT 0,
    detail TEXT,
    last_verified TEXT NOT NULL DEFAULT (date('now')),
    source_url TEXT,
    UNIQUE(competitor_id, feature)
);

-- Append-only audit log of every daily scan finding (raw data)
CREATE TABLE IF NOT EXISTS daily_scans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scanned_at TEXT NOT NULL DEFAULT (datetime('now')),
    competitor_id INTEGER REFERENCES competitors(id) ON DELETE SET NULL,
    query TEXT NOT NULL,
    headline TEXT,
    url TEXT,
    announced_feature TEXT,
    impact TEXT,
    librebase_delta TEXT,
    raw_snippet TEXT,
    parse_confidence REAL
);

-- Daily digest artifacts (the rendered report, stored in DB)
CREATE TABLE IF NOT EXISTS daily_digests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    digest_date TEXT NOT NULL UNIQUE,
    markdown TEXT NOT NULL,
    summary_json TEXT,            -- JSON with key takeaways, totals, etc.
    source_file TEXT,             -- path to the .md file (if written)
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Feature change history (deltas over time)
CREATE TABLE IF NOT EXISTS competitor_feature_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    competitor_id INTEGER NOT NULL REFERENCES competitors(id) ON DELETE CASCADE,
    feature TEXT NOT NULL,
    old_state INTEGER,
    new_state INTEGER NOT NULL,
    changed_at TEXT NOT NULL DEFAULT (datetime('now')),
    reason TEXT,
    source_url TEXT
);

-- New-competitor discovery log
CREATE TABLE IF NOT EXISTS discovery_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scanned_at TEXT NOT NULL DEFAULT (datetime('now')),
    query TEXT NOT NULL,
    candidate_name TEXT,
    candidate_url TEXT,
    disposition TEXT NOT NULL,
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_scans_at ON daily_scans(scanned_at);
CREATE INDEX IF NOT EXISTS idx_scans_comp ON daily_scans(competitor_id);
CREATE INDEX IF NOT EXISTS idx_cf_comp ON competitor_features(competitor_id);
CREATE INDEX IF NOT EXISTS idx_cf_feature ON competitor_features(feature);
CREATE INDEX IF NOT EXISTS idx_digests_date ON daily_digests(digest_date);
"""


# ── Seed: competitors ───────────────────────────────────────────────────

COMPETITORS = [
    # (name, url, category, notes)
    ("Supabase", "https://supabase.com", "BaaS",
     "Direct competitor — Supabase-shaped stack (Postgres, auth, storage, Realtime, Edge Functions, self-host). "
     "Largest open-source BaaS. Recently adding AI/ML features. We track them most closely."),
    ("Appwrite", "https://appwrite.io", "BaaS",
     "Open-source BaaS, self-host via Docker, auth + DB + storage + functions + multi-platform SDKs. "
     "PHP/Node stack. No agent/MCP story observed."),
    ("Firebase", "https://firebase.google.com", "BaaS",
     "Google's BaaS: Auth, Firestore, Storage, Cloud Functions, ML. Proprietary, vendor lock-in, "
     "no self-host option. Not agent-first."),
    ("PocketBase", "https://pocketbase.io", "BaaS",
     "Single-binary, self-host, Go-based. Auth + DB (sqlite) + storage + realtime. Very lightweight. "
     "Small team, limited feature set, no MCP/agent API. Overlaps on simplicity + self-host angle."),
    ("Nhost", "https://nhost.io", "BaaS",
     "PostgreSQL + GraphQL (Hasura) + auth + storage + serverless functions. GraphQL-centric. "
     "No agent/MCP story observed."),
    ("Directus", "https://directus.io", "CMS-overlap",
     "Headless CMS + instant REST/GraphQL API on any SQL DB. Overlaps on 'wrap your DB with an API' "
     "angle but more CMS-focused. No agent/MCP story observed."),
    ("Xano", "https://xano.com", "BaaS",
     "No-code backend: Postgres + API + functions + auth. Hosted only. Targeted at no-code builders. "
     "No agent/MCP story observed."),
    ("Railway", "https://railway.app", "PaaS",
     "PaaS with DBs + services + preview environments. Overlaps on 'run your backend on infra we manage' "
     "but not a BaaS. Instance-provisioning overlap with LibreBase."),
    ("Render", "https://render.com", "PaaS",
     "PaaS: web services, static sites, DBs, cron. Similar overlap to Railway on infra vs BaaS boundary."),
    ("Fly.io", "https://fly.io", "PaaS",
     "Close-to-metal PaaS, runs Docker containers on global edge. Overlaps on instance-hosting model. "
     "Not a BaaS but competes for 'where does my backend run' budget."),
    ("Heroku", "https://www.heroku.com", "PaaS",
     "Classic PaaS. Salesforce-owned. Still relevant for 'managed runtime' angle but declining relative to "
     "Railway/Render/Fly."),
    ("AWS Amplify", "https://aws.amazon.com/amplify/", "BaaS",
     "AWS's BaaS-ish offering: Auth, API (GraphQL/REST), storage, hosting, functions. "
     "Heavy AWS lock-in. Not agent-first."),
    ("Koywe", "https://koywe.com", "BaaS",
     "Latin-American BaaS, lighter traction. Watch for regional expansion."),
]

# ── Seed: our positioning ───────────────────────────────────────────────

OUR_POSITIONING = [
    # (feature, our_offer, strength, notes)
    ("postgresql-db", "lidb — Supabase-shaped Postgres stack with org/project/workspace workflows", "strong",
     "Core offering. Supabase-compatible shape so migration path exists for Supabase users."),
    ("auth", "Console auth: email/password (Argon2id), OAuth SSO (GitHub + Google), MFA TOTP, roles, sessions + refresh", "strong",
     "Full auth suite including MFA and OAuth SSO. Auto-provisions user + personal org on sign-up."),
    ("storage", "Supabase self-hosted storage (via self-hosted Supabase on VPS)", "neutral",
     "Available via self-hosted Supabase integration; not yet a first-class standalone surface."),
    ("realtime", "Not yet a first-class surfaced feature", "weak",
     "Supabase-shaped stack has Realtime under the hood but LibreBase has not marketed/surfaced it prominently."),
    ("mcp-agent-api", "Hosted MCP endpoint (app.librebase.xyz/api/mcp) + local MCP server; 15 tools: org/projects/instances/members/hosts + auth providers", "strong",
     "KEY DIFFERENTIATOR. Agent-first design: auto-discoverable via .well-known/mcp.json, docs at /for-agents + llms.txt. Most competitors have no MCP story."),
    ("agent-docs", "Dedicated agent docs (/for-agents) + llms.txt for LLM consumption", "strong",
     "KEY DIFFERENTIATOR. Explicit agent-consumable surface most BaaS competitors lack."),
    ("self-host", "Full self-host: Docker Compose on VPS, nginx, certbot TLS; separate staging stack; Supabase self-hosted on same VPS", "strong",
     "Self-host is a first-class path, not an afterthought. Staging isolated with separate Postgres + JWT secrets."),
    ("kubernetes", "K8s runtime: Helm chart (librebase-instance), reference manifests (dedicated + shared), k8s-provisioner in Studio", "strong",
     "K8s is a first-class runtime target, not a bolt-on. Dedicated + shared deployment models."),
    ("container-runtime", "licontainer — pure-Li OCI engine (no Rust, no C). Studio: LIBREBASE_RUNTIME=licontainer. K8s: Helm containerRuntime=licontainer.", "strong",
     "UNIQUE. Pure-Li container runtime is a genuine technical differentiator vs competitors' Docker/K8s-only story."),
    ("billing-plans", "Stripe billing: starter $29 (1 inst), pro $69 (3 inst), unlimited, self-host. Edition feature gates + quota enforcement. Discount codes.", "neutral",
     "Billing exists (checkout/portal/webhook/metering) but UI for 'upgrade plan' is still open. Metering is best-effort."),
    ("open-source", "Public repo (librebase-official/librebase on GitHub + GitLab origin). Studio, admin-api, kms, mcp, deploy, docs all public.", "strong",
     "Open-source with public repo. Some surfaces private (landing)."),
    ("console-studio", "Librebase Studio — Next.js web console: projects grid, instances list + health, project home + launch DB, K8s deploy flow", "neutral",
     "Studio is functional for core flows. E2E testing planned (Playwright). Some UI gaps (upgrade-plan UI)."),
    ("edge-functions", "Not yet surfaced as a first-class feature", "weak",
     "No edge function runtime marketed. Supabase Has Edge Functions; we don't yet."),
    ("graphql", "Not surfaced as a first-class API layer", "weak",
     "Supabase/Nhost offer GraphQL; LibreBase is SQL/REST-centric today."),
    ("row-level-security", "Via self-hosted Supabase (Postgres RLS under the hood)", "neutral",
     "Available through Supabase self-hosted integration but not a differentiated LibreBase feature."),
    ("vector-embeddings", "Not yet surfaced", "weak",
     "AI/ML vector search not yet a surfaced feature. Supabase has pgvector + AI extensions."),
    ("instance-model", "Dedicated (1 inst→1 project) + shared (1 inst→N projects) deployment models", "strong",
     "Flexible instance model is a genuine architectural choice most BaaS don't offer (they're typically single-tenant-per-project)."),
    ("kms-crypto", "Envelope AES-GCM + Ed25519 KMS (Python interim + pure-Li in lic). Exploit tests in test_kms_exploits.py.", "strong",
     "Bring-your-own-crypto with verified selftests. Pure-Li KMS is a unique trust story."),
    ("billing-metering", "Best-effort Stripe usage reporting on instance launch (when LIBREBASE_STRIPE_METERED_PRICE set)", "weak",
     "Metering is best-effort, not comprehensive. Room to improve."),
    ("discounts-codes", "Discount code redemption (TEST-UNLIMITED, EARLY-ADOPTER, …) → plan mapping", "neutral",
     "Exists but limited set of codes."),
    ("waitlist", "Waitlist via Supabase librebase_waitlist table; landing proxies to Studio waitlist endpoint", "neutral",
     "Functional for now; could be a first-class growth surface."),
    ("multi-region", "Not yet surfaced", "weak",
     "Single-region today (VPS in IONOS). Instance lifecycle Phase 3 mentions region scheduling."),
    ("custom-domains", "Not yet surfaced for instances (Phase 3 item)", "weak",
     "Planned for instance lifecycle Phase 3 (subdomain/ACME + custom domain)."),
    ("delete-endpoints", "Admin-api has launch/stop + provider delete only; no instance/project/host delete endpoints yet", "weak",
     "Open item. MCP delete tools gated on this."),
]


# ── Seed: competitor features (initial assessment; will be updated by scans) ──

COMPETITOR_FEATURES_SEED = {
    # competitor_name: {feature: (offered_int, detail)}
    "Supabase": {
        "postgresql-db": (1, "Core: managed Postgres with Dashboard, SQL editor, migrations. pgvector + extensions."),
        "auth": (1, "GoTrue-based email/password + OAuth (Google, GitHub, etc.) + MFA + SSO (enterprise)."),
        "storage": (1, "Managed object storage with policies, like S3-lite."),
        "realtime": (1, "Postgres-Realtime: broadcast + presence + DB change subscriptions."),
        "mcp-agent-api": (0, "No MCP endpoint or agent-first API surface observed as of 2026-08."),
        "agent-docs": (0, "No dedicated agent/LLM-consumable docs surface observed."),
        "self-host": (1, "Self-host via Docker Compose / Kubernetes (supabase/self-hosted repo). Heavy but doable."),
        "kubernetes": (1, "Self-host K8s via community Helm + their docker-compose; not as polished as hosted."),
        "container-runtime": (0, "No custom container runtime. Uses Docker/K8s primitives."),
        "billing-plans": (1, "Hosted: free tier + pro ($25/mo) + team + enterprise. Self-host is free (you pay infra)."),
        "open-source": (1, "Core is open-source (Apache 2.0). Some managed features are proprietary."),
        "console-studio": (1, "Mature dashboard: tables, auth, storage, functions, replication, backups."),
        "edge-functions": (1, "Edge Functions: Deno-based serverless functions, deployed globally."),
        "graphql": (1, "GraphQL via Supabase GraphQL extension / 3rd-party; not core but available."),
        "row-level-security": (1, "Postgres RLS is central to Supabase security model."),
        "vector-embeddings": (1, "pgvector + AI extensions (embeddings, text-to-SQL, etc.) — actively adding AI features."),
        "instance-model": (0, "No dedicated/shared instance model — it's a multi-tenant managed service or self-hosted monolith."),
        "kms-crypto": (0, "No customer-controlled KMS / envelope crypto story observed."),
        "billing-metering": (1, "Usage-based billing on pro/team; metering exists for hosted."),
        "discounts-codes": (0, "No prominent public discount-code system observed."),
        "waitlist": (0, "No waitlist — product is live."),
        "multi-region": (1, "Multi-region for hosted (AWS/GCP regions); self-host is your choice."),
        "custom-domains": (1, "Custom domains for projects, API URLs, etc."),
        "delete-endpoints": (1, "Full CRUD on most resources via dashboard + API."),
    },
    "Appwrite": {
        "postgresql-db": (0, "Uses MySQL / Appwrite DB (not Postgres). Different DB engine."),
        "auth": (1, "Full auth: email/password, OAuth, MFA, sessions, hooks."),
        "storage": (1, "File storage with permissions."),
        "realtime": (1, "Realtime subscriptions for DB + storage + channels."),
        "mcp-agent-api": (0, "No MCP/agent API observed."),
        "agent-docs": (0, "No dedicated agent docs observed."),
        "self-host": (1, "Single Docker Compose self-host. Very easy to self-host (their key pitch)."),
        "kubernetes": (0, "Self-host is Docker Compose; no polished K8s story."),
        "container-runtime": (0, "No custom container runtime."),
        "billing-plans": (1, "Cloud: free + paid plans. Self-host is free."),
        "open-source": (1, "Open-source (BSD 3-Clause)."),
        "console-studio": (1, "Mature console: projects, collections, functions, storage, auth."),
        "edge-functions": (1, "Cloud Functions: Node.js/Deno/Python/Go/Bun, deployed per-project."),
        "graphql": (0, "No native GraphQL (REST only, with SDKs)."),
        "row-level-security": (0, "Permission model is Appwrite's own (not Postgres RLS)."),
        "vector-embeddings": (0, "No vector/search AI features observed as core."),
        "instance-model": (0, "Single-tenant-per-project self-host or cloud; no dedicated/shared split."),
        "kms-crypto": (0, "No customer-controlled KMS story."),
        "billing-metering": (0, "Self-host is free (no metering); cloud has plan limits."),
        "discounts-codes": (0, "No prominent public discount-code system."),
        "waitlist": (0, "Product is live."),
        "multi-region": (0, "Self-host is single-region; cloud regions available."),
        "custom-domains": (1, "Custom domains for API + storage."),
        "delete-endpoints": (1, "Full CRUD via console + API."),
    },
    "Firebase": {
        "postgresql-db": (0, "Firestore (NoSQL document DB) + Realtime DB. Not Postgres."),
        "auth": (1, "Full auth: email/password, all OAuth providers, MFA, SSO (enterprise), custom claims."),
        "storage": (1, "Cloud Storage with security rules."),
        "realtime": (1, "Firestore realtime sync + Realtime Database."),
        "mcp-agent-api": (0, "No MCP/agent API observed."),
        "agent-docs": (0, "No dedicated agent docs."),
        "self-host": (0, "No self-host. Fully managed, Google Cloud only."),
        "kubernetes": (0, "No K8s story (it's a managed service, not something you run on K8s)."),
        "container-runtime": (0, "No custom container runtime."),
        "billing-plans": (1, "Pay-as-you-go (Blaze plan) + free tier. Can get expensive; opaque pricing at scale."),
        "open-source": (0, "Proprietary. SDKs open but service is not."),
        "console-studio": (1, "Mature console: projects, Firestore, auth, storage, functions, analytics, crashlytics."),
        "edge-functions": (1, "Cloud Functions (1st/2nd gen) + Cloud Run integration."),
        "graphql": (0, "Firestore isn't GraphQL-native; 3rd-party layers exist."),
        "row-level-security": (0, "Firestore security rules (not RLS). Different model."),
        "vector-embeddings": (1, "Vertex AI integration, embedding generation, search. Actively adding AI."),
        "instance-model": (0, "No dedicated/shared instance model."),
        "kms-crypto": (1, "Cloud KMS (separate product) for key management — but not envelope-crypto-as-a-feature."),
        "billing-metering": (1, "Fine-grained usage metering on Blaze plan."),
        "discounts-codes": (0, "No public discount codes."),
        "waitlist": (0, "Live."),
        "multi-region": (1, "Multi-region Firestore + Cloud Storage + Functions."),
        "custom-domains": (1, "Custom domains for Hosting + API."),
        "delete-endpoints": (1, "Full CRUD via console + Admin SDK."),
    },
    "PocketBase": {
        "postgresql-db": (0, "Uses SQLite (not Postgres). Single-file DB."),
        "auth": (1, "Auth: email/password, OAuth (Google, GitHub, etc.), JWT, optional MFA via plugin."),
        "storage": (1, "File storage (S3-compatible bucket or local)."),
        "realtime": (1, "Realtime subscriptions via WebSockets."),
        "mcp-agent-api": (0, "No MCP/agent API observed."),
        "agent-docs": (0, "No dedicated agent docs."),
        "self-host": (1, "Single binary self-host. Their core pitch: one executable, zero deps."),
        "kubernetes": (0, "No K8s story — single binary doesn't need K8s but also doesn't leverage it."),
        "container-runtime": (0, "No custom container runtime."),
        "billing-plans": (0, "Free/open-source; no hosted paid tier (you host it yourself)."),
        "open-source": (1, "Open-source (MIT)."),
        "console-studio": (1, "Minimal but functional admin UI: collections, auth, settings, file manager."),
        "edge-functions": (0, "No edge functions. Hooks via Go plugins (self-host only)."),
        "graphql": (0, "REST API only (no native GraphQL)."),
        "row-level-security": (0, "PocketBase permissions model (not RLS)."),
        "vector-embeddings": (0, "No vector/AI features."),
        "instance-model": (0, "Single instance = single DB. No dedicated/shared model."),
        "kms-crypto": (0, "No customer-controlled KMS story."),
        "billing-metering": (0, "No billing (free self-host)."),
        "discounts-codes": (0, "N/A."),
        "waitlist": (0, "Live."),
        "multi-region": (0, "Single-instance; you replicate/cluster yourself (not built-in)."),
        "custom-domains": (1, "Reverse proxy in front; custom domains via your own nginx."),
        "delete-endpoints": (1, "Full CRUD via admin UI + API."),
    },
    "Nhost": {
        "postgresql-db": (1, "Core: managed Postgres (via Hasura + their stack)."),
        "auth": (1, "Auth: email/password, OAuth, MFA via GoTrue (Supabase-compatible)."),
        "storage": (1, "File storage with policies."),
        "realtime": (1, "GraphQL subscriptions (via Hasura) for realtime."),
        "mcp-agent-api": (0, "No MCP/agent API observed."),
        "agent-docs": (0, "No dedicated agent docs."),
        "self-host": (0, "Primarily hosted; self-host possible but not their main pitch."),
        "kubernetes": (0, "No prominent K8s story."),
        "container-runtime": (0, "No custom container runtime."),
        "billing-plans": (1, "Hosted tiers: free + growth + scale. Usage-based."),
        "open-source": (1, "Core components open-source (Hasura, GoTrue, etc.)."),
        "console-studio": (1, "Console: DB, GraphQL, auth, storage, functions."),
        "edge-functions": (1, "Serverless functions (Node.js)."),
        "graphql": (1, "Core: Hasura-based GraphQL (their main API surface)."),
        "row-level-security": (1, "Postgres RLS + Hasura permissions."),
        "vector-embeddings": (0, "No prominent vector/AI features observed."),
        "instance-model": (0, "No dedicated/shared model."),
        "kms-crypto": (0, "No customer-controlled KMS story."),
        "billing-metering": (1, "Usage-based metering on hosted plans."),
        "discounts-codes": (0, "No prominent public discount codes."),
        "waitlist": (0, "Live."),
        "multi-region": (1, "Multi-region hosted."),
        "custom-domains": (1, "Custom domains for API + storage."),
        "delete-endpoints": (1, "Full CRUD via console + GraphQL API."),
    },
    "Directus": {
        "postgresql-db": (1, "Wraps any SQL DB (Postgres, MySQL, SQLite, etc.) — you bring the DB."),
        "auth": (1, "Auth: email/password, OAuth, JWT, SSO (enterprise)."),
        "storage": (1, "File storage (local + S3-compatible)."),
        "realtime": (1, "Realtime via WebSockets (optional)."),
        "mcp-agent-api": (0, "No MCP/agent API observed."),
        "agent-docs": (0, "No dedicated agent docs (though they have extensive REST/GraphQL docs)."),
        "self-host": (1, "Self-host via Docker/npm. Very flexible."),
        "kubernetes": (0, "No prominent K8s story (Docker/npm self-host works on K8s but not a first-class Helm chart)."),
        "container-runtime": (0, "No custom container runtime."),
        "billing-plans": (1, "Cloud (Directus Cloud) + enterprise self-host support. Open-source core is free."),
        "open-source": (1, "Open-source (GPL 3.0 for core; enterprise is separate)."),
        "console-studio": (1, "Very mature no-code admin app: collections, relations, flows, dashboard, extensions."),
        "edge-functions": (1, "Flows + extensions + serverless functions (self-host + cloud)."),
        "graphql": (1, "GraphQL API auto-generated from your schema (core feature)."),
        "row-level-security": (0, "Directus permissions/roles model (not Postgres RLS)."),
        "vector-embeddings": (0, "No vector/AI features as core (they have AI extensions in progress)."),
        "instance-model": (0, "No dedicated/shared model — it's a single app wrapping your DB."),
        "kms-crypto": (0, "No customer-controlled KMS story."),
        "billing-metering": (0, "Cloud has plan limits; self-host is free."),
        "discounts-codes": (0, "No prominent public discount codes."),
        "waitlist": (0, "Live."),
        "multi-region": (0, "Self-host is your choice; cloud is single-region (you replicate)."),
        "custom-domains": (1, "Custom domains for API + admin app."),
        "delete-endpoints": (1, "Full CRUD via admin app + API."),
    },
    "Xano": {
        "postgresql-db": (1, "Postgres under the hood (managed)."),
        "auth": (1, "Auth: email/password, OAuth, JWT, MFA."),
        "storage": (1, "File storage."),
        "realtime": (1, "WebSockets / realtime APIs (via their platform)."),
        "mcp-agent-api": (0, "No MCP/agent API observed."),
        "agent-docs": (0, "No dedicated agent docs."),
        "self-host": (0, "Hosted only. No self-host."),
        "kubernetes": (0, "No K8s story (hosted only)."),
        "container-runtime": (0, "No custom container runtime."),
        "billing-plans": (1, "Hosted tiers: free + paid (usage-based + plan limits). Can get expensive."),
        "open-source": (0, "Proprietary / hosted only."),
        "console-studio": (1, "No-code backend builder console: APIs, DB, functions, auth, workflows."),
        "edge-functions": (1, "Serverless functions + background tasks + webhooks."),
        "graphql": (1, "Auto-generated GraphQL + REST APIs."),
        "row-level-security": (0, "Xano's own permission model (not RLS)."),
        "vector-embeddings": (0, "No prominent vector/AI features."),
        "instance-model": (0, "No dedicated/shared model."),
        "kms-crypto": (0, "No customer-controlled KMS story."),
        "billing-metering": (1, "Usage-based metering on paid plans."),
        "discounts-codes": (0, "No prominent public discount codes."),
        "waitlist": (0, "Live."),
        "multi-region": (0, "Single-region hosted."),
        "custom-domains": (1, "Custom domains for APIs."),
        "delete-endpoints": (1, "Full CRUD via console + API."),
    },
    "Railway": {
        "postgresql-db": (1, "Managed Postgres (one-click deploy). Also MySQL, Redis, etc."),
        "auth": (0, "No built-in auth — you bring your own (it's infra, not BaaS)."),
        "storage": (0, "No built-in object storage — you bring your own (S3, etc.)."),
        "realtime": (0, "No built-in realtime — you build it."),
        "mcp-agent-api": (0, "No MCP/agent API observed."),
        "agent-docs": (0, "No dedicated agent docs (though they have good infra docs)."),
        "self-host": (0, "Hosted only (no self-host)."),
        "kubernetes": (0, "No K8s story (they run your services on their infra)."),
        "container-runtime": (0, "Runs your Docker containers; no custom runtime."),
        "billing-plans": (1, "Pay-as-you-go (usage-based). $5 credit to start. Can scale up quickly."),
        "open-source": (0, "Proprietary platform (hosted only)."),
        "console-studio": (1, "Modern console: projects, services, DBs, deployments, logs, variables."),
        "edge-functions": (1, "Deploy any service (Docker/nginx/etc.); Functions via your own code."),
        "graphql": (0, "No built-in GraphQL — you bring your own."),
        "row-level-security": (0, "Not applicable (infra, not DB platform)."),
        "vector-embeddings": (0, "No built-in vector/AI (but you can run any stack)."),
        "instance-model": (0, "No dedicated/shared model — it's 'deploy services'."),
        "kms-crypto": (0, "No KMS story (you bring your own secrets via variables)."),
        "billing-metering": (1, "Fine-grained usage metering (CPU/RAM/network per service)."),
        "discounts-codes": (0, "No prominent public discount codes."),
        "waitlist": (0, "Live."),
        "multi-region": (1, "Multi-region deployment (choose region per service)."),
        "custom-domains": (1, "Custom domains per service."),
        "delete-endpoints": (1, "Full lifecycle: create/start/stop/delete services + DBs."),
    },
    "Render": {
        "postgresql-db": (1, "Managed Postgres (also MySQL). One-click."),
        "auth": (0, "No built-in auth."),
        "storage": (0, "No built-in object storage (Blob storage for static sites only)."),
        "realtime": (0, "No built-in realtime."),
        "mcp-agent-api": (0, "No MCP/agent API."),
        "agent-docs": (0, "No dedicated agent docs."),
        "self-host": (0, "Hosted only."),
        "kubernetes": (0, "No K8s (they run your services)."),
        "container-runtime": (0, "Runs your Docker containers / native services."),
        "billing-plans": (1, "Pay-as-you-go + free tier for services/DBs (with limits). Static sites free."),
        "open-source": (0, "Proprietary."),
        "console-studio": (1, "Console: services, static sites, DBs, cron jobs, logs, metrics."),
        "edge-functions": (0, "No edge functions (you deploy services)."),
        "graphql": (0, "No built-in GraphQL."),
        "row-level-security": (0, "N/A (infra)."),
        "vector-embeddings": (0, "No built-in vector/AI."),
        "instance-model": (0, "No dedicated/shared model."),
        "kms-crypto": (0, "No KMS (environment variables for secrets)."),
        "billing-metering": (1, "Usage-based metering."),
        "discounts-codes": (0, "No prominent public discount codes."),
        "waitlist": (0, "Live."),
        "multi-region": (1, "Multi-region (choose region per service)."),
        "custom-domains": (1, "Custom domains per service."),
        "delete-endpoints": (1, "Full lifecycle management."),
    },
    "Fly.io": {
        "postgresql-db": (1, "Managed Postgres (Fly Postgres) — multi-region clusters."),
        "auth": (0, "No built-in auth."),
        "storage": (1, "Voluntary: Fly Volumes (block storage) + you bring S3/etc."),
        "realtime": (0, "No built-in realtime (you build it)."),
        "mcp-agent-api": (0, "No MCP/agent API."),
        "agent-docs": (0, "No dedicated agent docs (good infra docs though)."),
        "self-host": (0, "Hosted only (but very close to metal — you control the VM basically)."),
        "kubernetes": (0, "No K8s (they have their own orchestrator; K8s is not the model)."),
        "container-runtime": (0, "Runs your Docker containers on Firecracker micro-VMs."),
        "billing-plans": (1, "Pay-as-you-go (very granular: per-VM, per-volume, per-bandwidth). $5 credit."),
        "open-source": (0, "Proprietary platform."),
        "console-studio": (1, "Console: apps, volumes, machines, secrets, IPs, logs."),
        "edge-functions": (0, "No edge functions (you deploy apps close to users)."),
        "graphql": (0, "No built-in GraphQL."),
        "row-level-security": (0, "N/A (infra)."),
        "vector-embeddings": (0, "No built-in vector/AI (but you can run anything)."),
        "instance-model": (0, "No dedicated/shared model — it's 'deploy machines'."),
        "kms-crypto": (0, "No KMS (secrets via fly secrets)."),
        "billing-metering": (1, "Very granular usage metering."),
        "discounts-codes": (0, "No prominent public discount codes."),
        "waitlist": (0, "Live (invite-only historically, now open)."),
        "multi-region": (1, "Core pitch: deploy close to users, multi-region clusters."),
        "custom-domains": (1, "Custom domains + TLS per app."),
        "delete-endpoints": (1, "Full lifecycle: machines, volumes, apps, IPs."),
    },
    "Heroku": {
        "postgresql-db": (1, "Managed Postgres (Heroku Postgres) — mature, many plans."),
        "auth": (0, "No built-in auth."),
        "storage": (0, "No built-in object storage (s3 via add-ons)."),
        "realtime": (0, "No built-in realtime."),
        "mcp-agent-api": (0, "No MCP/agent API."),
        "agent-docs": (0, "No dedicated agent docs."),
        "self-host": (0, "Hosted only."),
        "kubernetes": (0, "Heroku CI + Docker build; no K8s runtime (they had Heroku Container Registry)."),
        "container-runtime": (0, "Runs your Docker containers / buildpacks."),
        "billing-plans": (1, "Tiered plans (eco, hobby, professional, premier) + add-ons. Pricing opaque at higher tiers."),
        "open-source": (0, "Proprietary (Salesforce-owned)."),
        "console-studio": (1, "Mature console: apps, add-ons, pipelines, logs, metrics."),
        "edge-functions": (0, "No edge functions (you deploy apps)."),
        "graphql": (0, "No built-in GraphQL."),
        "row-level-security": (0, "N/A (infra)."),
        "vector-embeddings": (0, "No built-in vector/AI (add-ons only)."),
        "instance-model": (0, "No dedicated/shared model."),
        "kms-crypto": (0, "No KMS (config vars for secrets)."),
        "billing-metering": (1, "Metering on higher tiers; hobby is flat-rate."),
        "discounts-codes": (0, "No prominent public discount codes."),
        "waitlist": (0, "Live."),
        "multi-region": (1, "Multi-region for Postgres; app regions available."),
        "custom-domains": (1, "Custom domains per app."),
        "delete-endpoints": (1, "Full lifecycle: apps, add-ons, pipelines."),
    },
    "AWS Amplify": {
        "postgresql-db": (1, "AWS AppSync (GraphQL) + DynamoDB/RDS; Amplify Data connects to both."),
        "auth": (1, "Cognito-based auth: email/password, all OAuth, MFA, SSO, custom claims."),
        "storage": (1, "S3 + CloudFront via Amplify Storage."),
        "realtime": (1, "AppSync realtime subscriptions (GraphQL)."),
        "mcp-agent-api": (0, "No MCP/agent API."),
        "agent-docs": (0, "No dedicated agent docs (extensive AWS docs but not agent-first)."),
        "self-host": (0, "No self-host. Fully AWS-managed."),
        "kubernetes": (0, "No K8s story in Amplify (EKS is separate)."),
        "container-runtime": (0, "No custom runtime (Amplify Hosting = static/SSR; Functions = Lambda)."),
        "billing-plans": (1, "Pay-as-you-go (AWS pricing). Free tier available. Can be complex/opaque."),
        "open-source": (1, "Amplify CLI + libraries are open-source; the services are AWS managed."),
        "console-studio": (1, "Console: apps, auth, data, storage, functions, hosting, CI/CD."),
        "edge-functions": (1, "Lambda-based functions + AppSync resolvers."),
        "graphql": (1, "AppSync GraphQL (core API layer). Also REST via API Gateway."),
        "row-level-security": (0, "Cognito + AppSync auth rules (not RLS)."),
        "vector-embeddings": (1, "Amazon Bedrock / Titan embeddings / OpenSearch vector search — deep AWS AI integration."),
        "instance-model": (0, "No dedicated/shared model."),
        "kms-crypto": (1, "AWS KMS is available (separate service) — strong crypto story but not envelope-crypto-as-a-BaaS-feature."),
        "billing-metering": (1, "Fine-grained AWS metering (per-service)."),
        "discounts-codes": (0, "No public discount codes (AWS credits for startups)."),
        "waitlist": (0, "Live."),
        "multi-region": (1, "Multi-region via AWS global infra."),
        "custom-domains": (1, "Custom domains for Hosting + API."),
        "delete-endpoints": (1, "Full CRUD via console + CLI."),
    },
    "Koywe": {
        "postgresql-db": (1, "Managed Postgres (their backend-as-a-service)."),
        "auth": (1, "Auth included."),
        "storage": (1, "Storage included."),
        "realtime": (0, "Not prominently advertised."),
        "mcp-agent-api": (0, "No MCP/agent API observed."),
        "agent-docs": (0, "No dedicated agent docs."),
        "self-host": (0, "Hosted only ( LatAm-focused)."),
        "kubernetes": (0, "No prominent K8s story."),
        "container-runtime": (0, "No custom runtime."),
        "billing-plans": (1, "Hosted tiers (LatAm market)."),
        "open-source": (0, "Proprietary / hosted."),
        "console-studio": (1, "Console for managing backend resources."),
        "edge-functions": (1, "Serverless functions included."),
        "graphql": (0, "REST-focused (no prominent GraphQL)."),
        "row-level-security": (0, "Their own permission model."),
        "vector-embeddings": (0, "No vector/AI observed."),
        "instance-model": (0, "No dedicated/shared model."),
        "kms-crypto": (0, "No KMS story."),
        "billing-metering": (0, "Plan-based; metering not prominently advertised."),
        "discounts-codes": (0, "No prominent public discount codes."),
        "waitlist": (0, "Live."),
        "multi-region": (0, "Single-region (LatAm)."),
        "custom-domains": (1, "Custom domains supported."),
        "delete-endpoints": (1, "CRUD via console + API."),
    },
}


# ── Helpers ─────────────────────────────────────────────────────────────

def get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_conn()
    conn.executescript(SCHEMA)
    return conn


def seed_competitors(conn):
    cur = conn.cursor()
    now = date.today().isoformat()
    for name, url, category, notes in COMPETITORS:
        cur.execute(
            "INSERT OR IGNORE INTO competitors (name, url, category, first_seen, notes) VALUES (?,?,?,?,?)",
            (name, url, category, now, notes),
        )
    return cur.rowcount


def seed_our_positioning(conn):
    cur = conn.cursor()
    now = date.today().isoformat()
    for feature, offer, strength, notes in OUR_POSITIONING:
        cur.execute(
            """INSERT INTO our_positioning (feature, our_offer, strength, notes, updated_at)
               VALUES (?,?,?,?,?)
               ON CONFLICT(feature) DO UPDATE SET
                   our_offer=excluded.our_offer,
                   strength=excluded.strength,
                   notes=excluded.notes,
                   updated_at=excluded.updated_at""",
            (feature, offer, strength, notes, now),
        )
    return cur.rowcount


def seed_competitor_features(conn):
    cur = conn.cursor()
    now = date.today().isoformat()
    # Build name→id map
    rows = conn.execute("SELECT id, name FROM competitors").fetchall()
    name_to_id = {r["name"]: r["id"] for r in rows}

    inserted = 0
    for comp_name, features in COMPETITOR_FEATURES_SEED.items():
        cid = name_to_id.get(comp_name)
        if cid is None:
            print(f"WARNING: competitor '{comp_name}' not found in DB, skipping features")
            continue
        for feature, (offered, detail) in features.items():
            cur.execute(
                """INSERT INTO competitor_features (competitor_id, feature, offered, detail, last_verified, source_url)
                   VALUES (?,?,?,?,?,?)
                   ON CONFLICT(competitor_id, feature) DO UPDATE SET
                       offered=excluded.offered,
                       detail=excluded.detail,
                       last_verified=excluded.last_verified,
                       source_url=excluded.source_url""",
                (cid, feature, offered, detail, now, ""),
            )
            inserted += 1
    return inserted


def seed_all():
    conn = init_db()
    cc = seed_competitors(conn)
    op = seed_our_positioning(conn)
    cf = seed_competitor_features(conn)
    conn.commit()
    print(f"Seeded: {cc} competitors, {op} positioning rows, {cf} competitor-feature rows")
    print(f"DB path: {DB_PATH}")
    return conn


# ── CLI ──────────────────────────────────────────────────────────────────

def store_daily_digest(
    conn, date_str: str, markdown: str,
    summary_json=None, source_file=None,
):
    """Upsert the daily digest into daily_digests."""
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO daily_digests (digest_date, markdown, summary_json, source_file, created_at)
           VALUES (?,?,?,?,?)
           ON CONFLICT(digest_date) DO UPDATE SET
               markdown=excluded.markdown,
               summary_json=excluded.summary_json,
               source_file=excluded.source_file,
               created_at=excluded.created_at""",
        (date_str, markdown, summary_json, source_file, datetime.now().isoformat()),
    )
    conn.commit()
    return cur.lastrowid


def get_daily_digest(conn, date_str: str):
    """Return the digest row for a given date, or None."""
    row = conn.execute(
        "SELECT * FROM daily_digests WHERE digest_date = ?", (date_str,)
    ).fetchone()
    return dict(row) if row else None


def get_digest_range(conn, since: str, until=None):
    """Return digest rows between since and until (inclusive)."""
    if until is None:
        until = date.today().isoformat()
    rows = conn.execute(
        "SELECT * FROM daily_digests WHERE digest_date >= ? AND digest_date <= ? ORDER BY digest_date",
        (since, until),
    ).fetchall()
    return [dict(r) for r in rows]


if __name__ == "__main__":
    conn = seed_all()
    conn.close()
