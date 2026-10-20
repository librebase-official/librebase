# LibreBase Competitive Intelligence — Daily Scan Runner
# Runs every weekday 09:00 CEST (~07:00 UTC).
# Self-contained: performs web_search + web_extract itself, builds findings,
# persists them into librebase_competitive.db via the scan CLI, and delivers
# the digest to this chat (origin).
#
# DB: LIBREBASE_COMPATIVE_DB env (default ~/Documents/coding-projects/librebase/librebase_competitive.db)
# Scan CLI: librebase_competitive_scan.py (same dir as this DB)

import json, subprocess, os, datetime, textwrap

DB_DIR = "/Users/julian/Documents/coding-projects/librebase"
SCAN_CLI = os.path.join(DB_DIR, "librebase_competitive_scan.py")
DB_PATH = os.path.join(DB_DIR, "librebase_competitive.db")

# ── Competitor watchlist with per-competitor search queries ───────────────
# Format: (competitor_name, [queries])
# Queries are designed to surface recent announcements/features/benchmarks.

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

# ── New-competitor discovery queries ──────────────────────────────────────
DISCOVERY_QUERIES = [
    "new backend-as-a-service 2026 agent MCP",
    "new open source BaaS 2026 agent",
    "new developer platform 2026 AI agent backend",
    "alternative to supabase 2026 agent",
    "new postgress backend platform 2026",
    "self-host backend platform 2026 agent",
]


def run(cmd):
    """Run scan CLI, return stdout."""
    p = subprocess.run(
        ["/Users/julian/.local/bin/python3.11", SCAN_CLI] + cmd,
        capture_output=True, text=True, cwd=DB_DIR,
    )
    if p.returncode != 0:
        return f"ERROR (rc={p.returncode}): {p.stderr}"
    return p.stdout


def persist_findings(findings):
    p = subprocess.run(
        ["/Users/julian/.local/bin/python3.11", SCAN_CLI],
        input=json.dumps(findings),
        capture_output=True, text=True, cwd=DB_DIR,
    )
    if p.returncode != 0:
        return f"ERROR persisting findings (rc={p.returncode}): {p.stderr}"
    return p.stdout.strip()


def today():
    return datetime.date.today().isoformat()


# ── Step 1: search each competitor ────────────────────────────────────────
all_findings = []
seen_urls = set()

for comp, queries in COMPETITOR_QUERIES.items():
    for q in queries:
        results = __import__("hermes_tools").web_search(q, limit=5)
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
            # Heuristic: prioritize result that looks like an announcement/feature
            # We'll extract the top 1-2 promising pages per competitor per session.
            snippet = f"{title} — {desc[:300]}"
            # Create a finding for each result (confidence lower for just-search hits)
            feature_guess = ""
            impact_guess = "noise"
            # Quick mapping from query/title keywords to LibreBase feature
            title_lower = (title + desc).lower()
            if any(k in title_lower for k in ["mcp", "agent", "agentic", "agent sdk", "agent api"]):
                feature_guess = "mcp-agent-api"
                impact_guess = "strong"
            elif any(k in title_lower for k in ["eval", "benchmark", "agent performance", "agent test"]):
                feature_guess = "mcp-agent-api"
                impact_guess = "strong"
            elif any(k in title_lower for k in ["ai", "vector", "embedding", "pgvector", "ml", "llm"]):
                feature_guess = "vector-embeddings"
                impact_guess = "strong"
            elif any(k in title_lower for k in ["edge function", "serverless function", "cloud function", "@supabase/server"]):
                feature_guess = "edge-functions"
                impact_guess = "neutral"
            elif any(k in title_lower for k in ["pipeline", "etl", "cdc", "data pipeline", "bigquery"]):
                feature_guess = "postgresql-db"
                impact_guess = "strong"
            elif any(k in title_lower for k in ["pricing", "price", "cost", "plan", "tier"]):
                feature_guess = "billing-plans"
                impact_guess = "neutral"
            elif any(k in title_lower for k in ["roadmap", "changelog", "release", "update", "new feature", "announced", "launched", "shipping"]):
                feature_guess = ""  # general; let digest handle it
                impact_guess = "noise"
            else:
                feature_guess = ""
                impact_guess = "noise"

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
            # Only take 1-2 findings per competitor to avoid noise; break after first few
            if len([f for f in all_findings if f["competitor"] == comp]) >= 3:
                break
        if len([f for f in all_findings if f["competitor"] == comp]) >= 3:
            break

# ── Step 2: discovery queries (new competitors) ──────────────────────────
for q in DISCOVERY_QUERIES:
    results = __import__("hermes_tools").web_search(q, limit=5)
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

# ── Step 4: build + store digest in SQLite ──────────────────────────────
store_out = run(["--store-digest"])

# ── Step 5: status ──────────────────────────────────────────────────────
status = run(["--status"])

today_str = today()

output = textwrap.dedent(f"""
# LibreBase Competitive Intelligence — Daily Scan {today_str}

> **Täglicher Wettbewerbs-Report** — LibreBase Competitive Intelligence.
Scans heute: {len(COMPETITOR_QUERIES)} bekannte Mitbewerber + Discovery-Queries.

---

## DB Status
{status}

---

## Persisted
{store_out}
""").strip()

# The digest markdown lives now in daily_digests (SQLite) + competitive_digest_*.md (file).
# Re-read it from the file for display (the cron prompt runs in a Hermes agent context
# with file read access; we write it above via --store-digest + file).

digest_path = os.path.join(DB_DIR, f"competitive_digest_{today_str}.md")
if os.path.exists(digest_path):
    with open(digest_path, "r") as f:
        digest_md = f.read()
    output += f"\n\n{digest_md}"

print(f"Stored: {store_out}")
print(f"\n=== FULL REPORT ===\n{output}")
