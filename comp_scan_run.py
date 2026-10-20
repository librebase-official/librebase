#!/usr/bin/env /Users/julian/.local/bin/python3.11
"""LibreBase Competitive Intelligence Daily Scan."""
import json, subprocess, os, datetime, textwrap, sys
sys.path.insert(0, "/Users/julian/.local/lib/python3.11/site-packages")

# Hermes tools are available as a package
from hermes_tools import web_search, web_extract

DB_DIR = "/Users/julian/Documents/coding-projects/librebase"
SCAN_CLI = os.path.join(DB_DIR, "librebase_competitive_scan.py")
PYTHON = "/Users/julian/.local/bin/python3.11"

def run_scan(cmd):
    p = subprocess.run([PYTHON, SCAN_CLI] + cmd, capture_output=True, text=True, cwd=DB_DIR)
    if p.returncode != 0:
        return f"ERROR (rc={p.returncode}): {p.stderr}"
    return p.stdout.strip()

def persist_findings(findings):
    p = subprocess.run([PYTHON, SCAN_CLI], input=json.dumps(findings), capture_output=True, text=True, cwd=DB_DIR)
    if p.returncode != 0:
        return f"ERROR persisting (rc={p.returncode}): {p.stderr}"
    return p.stdout.strip()

def today():
    return datetime.date.today().isoformat()

# ── Watchlist: competitor → search queries ───────────────────────────────
COMPETITOR_QUERIES = {
    "Supabase": [
        "supabase new features 2026 site:supabase.com/blog",
        "supabase MCP server agent 2026",
        "supabase evals benchmark 2026",
        "supabase pricing changes 2026",
    ],
    "Appwrite": [
        "appwrite new features 2026 site:appwrite.io/blog",
        "appwrite MCP agent 2026",
        "appwrite pricing 2026",
        "appwrite changelog 2026",
    ],
    "Firebase": [
        "firebase new features 2026 site:firebase.google.com",
        "firebase MCP agent 2026",
        "firebase pricing changes 2026",
        "google cloud firebase updates 2026",
    ],
    "PocketBase": [
        "pocketbase new features 2026",
        "pocketbase roadmap 2026",
        "pocketbase MCP agent 2026",
        "pocketbase release 2026",
    ],
    "Nhost": [
        "nhost new features 2026 site:nhost.io",
        "nhost MCP agent 2026",
        "nhost GraphQL 2026",
        "nhost pricing 2026",
    ],
    "Directus": [
        "directus new features 2026 site:directus.io",
        "directus MCP agent 2026",
        "directus AI features 2026",
        "directus pricing 2026",
    ],
    "Xano": [
        "xano new features 2026 site:xano.com",
        "xano MCP agent 2026",
        "xano pricing 2026",
        "xano no-code backend 2026 updates",
    ],
    "Railway": [
        "railway new features 2026 site:railway.app",
        "railway MCP agent 2026",
        "railway pricing 2026",
        "railway database 2026",
    ],
    "Render": [
        "render new features 2026 site:render.com",
        "render MCP agent 2026",
        "render pricing 2026",
        "render database 2026",
    ],
    "Fly.io": [
        "fly.io new features 2026 site:fly.io",
        "fly.io MCP agent 2026",
        "fly.io postgres 2026",
        "fly.io pricing 2026",
    ],
    "Heroku": [
        "heroku new features 2026 site:heroku.com",
        "heroku MCP agent 2026",
        "heroku pricing 2026",
        "heroku postgres 2026",
    ],
    "AWS Amplify": [
        "AWS Amplify new features 2026 site:aws.amazon.com/amplify",
        "AWS Amplify MCP agent 2026",
        "AWS Amplify pricing 2026",
        "AWS Amplify AI features 2026",
    ],
    "Koywe": [
        "koywe new features 2026",
        "koywe MCP agent 2026",
        "koywe backend as a service 2026",
    ],
}

DISCOVERY_QUERIES = [
    "new backend-as-a-service 2026 agent MCP",
    "new open source BaaS 2026 agent",
    "new developer platform 2026 AI agent backend",
    "alternative to supabase 2026 agent",
    "new postgress backend platform 2026",
    "self-host backend platform 2026 agent",
]

# ── Step 1: search each competitor ────────────────────────────────────────
all_findings = []
seen_urls = set()

for comp, queries in COMPETITOR_QUERIES.items():
    for q in queries:
        results = web_search(q, limit=5)
        web_results = results.get("data", {}).get("web", [])
        if not web_results:
            continue
        for r in web_results:
            url = r.get("url", "")
            if url in seen_urls:
                continue
            seen_urls.add(url)
            title = r.get("title", "") or ""
            desc = r.get("description", "") or ""
            snippet = f"{title} — {desc[:300]}"
            title_lower = (title + desc).lower()

            # Map keywords → LibreBase feature + impact
            feature_guess = ""
            impact_guess = "noise"
            if any(k in title_lower for k in ["mcp", "agent", "agentic", "agent sdk", "agent api"]):
                feature_guess, impact_guess = "mcp-agent-api", "strong"
            elif any(k in title_lower for k in ["eval", "benchmark", "agent performance", "agent test"]):
                feature_guess, impact_guess = "mcp-agent-api", "strong"
            elif any(k in title_lower for k in ["ai", "vector", "embedding", "pgvector", "ml", "llm"]):
                feature_guess, impact_guess = "vector-embeddings", "strong"
            elif any(k in title_lower for k in ["edge function", "serverless function", "cloud function", "@supabase/server"]):
                feature_guess, impact_guess = "edge-functions", "neutral"
            elif any(k in title_lower for k in ["pipeline", "etl", "cdc", "data pipeline", "bigquery"]):
                feature_guess, impact_guess = "postgresql-db", "strong"
            elif any(k in title_lower for k in ["pricing", "price", "cost", "plan", "tier"]):
                feature_guess, impact_guess = "billing-plans", "neutral"
            elif any(k in title_lower for k in ["roadmap", "changelog", "release", "update", "new feature", "announced", "launched", "shipping"]):
                feature_guess, impact_guess = "", "noise"

            all_findings.append({
                "competitor": comp,
                "query": q,
                "headline": title if title else url,
                "url": url,
                "announced_feature": feature_guess,
                "impact": impact_guess,
                "librebase_delta": f"Watch: {title}" if feature_guess else "",
                "raw_snippet": snippet,
                "confidence": 0.65 if feature_guess else 0.45,
            })
            # cap at 3 findings per competitor
            if len([f for f in all_findings if f["competitor"] == comp]) >= 3:
                break
        if len([f for f in all_findings if f["competitor"] == comp]) >= 3:
            break

# ── Step 2: discovery queries ─────────────────────────────────────────────
for q in DISCOVERY_QUERIES:
    results = web_search(q, limit=5)
    web_results = results.get("data", {}).get("web", [])
    for r in web_results[:2]:
        url = r.get("url", "")
        if url in seen_urls:
            continue
        seen_urls.add(url)
        title = r.get("title", "") or ""
        desc = r.get("description", "") or ""
        all_findings.append({
            "competitor": "new",
            "competitor_url": url,
            "query": q,
            "headline": title if title else url,
            "url": url,
            "announced_feature": "mcp-agent-api" if any(k in (title + desc).lower() for k in ["mcp", "agent", "agentic"]) else "",
            "impact": "new-competitor",
            "librebase_delta": "New competitor candidate — evaluate whether to track",
            "raw_snippet": f"{title} — {desc[:300]}",
            "confidence": 0.5,
            "disposition": "uncertain",
        })

# ── Step 3: persist ──────────────────────────────────────────────────────
if all_findings:
    persist_out = persist_findings(all_findings)
else:
    persist_out = "No findings generated today."

# ── Step 4: digest + status ──────────────────────────────────────────────
digest = run_scan(["--digest"])
status = run_scan(["--status"])

today_str = today()
note = (
    "> **Automated daily scan** — Hermes cron at 09:00 CEST weekdays. "
    f"Scanned {len(COMPETITOR_QUERIES)} known competitors + discovery queries. "
    "Confidence scores are coarse heuristics; treat as directional."
)

output = textwrap.dedent(f"""
# LibreBase Competitive Intelligence — Daily Scan {today_str}

{note}

{digest}

---

## DB Status
{status}
""").strip()

# Write digest file
digest_path = os.path.join(DB_DIR, f"competitive_digest_{today_str}.md")
with open(digest_path, "w") as f:
    f.write(output + "\n")

print(f"Digest file: {digest_path}")
print(f"Persisted: {persist_out}")
print()
print(output)
