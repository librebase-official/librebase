#!/usr/bin/env /Users/julian/Documents/coding-projects/librebase/.venv/bin/python3
"""
LibreBase Competitive Intelligence Daily Scan — DDG HTML fallback.
Runs curl against DuckDuckGo HTML endpoint, parses results, feeds
findings to librebase_competitive_scan.py via stdin.
"""
import json, subprocess, re, os, datetime, sys, html as html_mod

DB_DIR = "/Users/julian/Documents/coding-projects/librebase"
SCAN_CLI = os.path.join(DB_DIR, "librebase_competitive_scan.py")
PYTHON = "/Users/julian/Documents/coding-projects/librebase/.venv/bin/python3"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def ddg_search(query: str, limit: int = 5) -> list:
    """Search DuckDuckGo HTML endpoint and return parsed results."""
    import urllib.parse
    encoded = urllib.parse.quote(query, safe='')
    url = f"https://html.duckduckgo.com/html/?q={encoded}"
    try:
        p = subprocess.run(
            ["curl", "-sL", url, "-o", "/tmp/ddg.html",
             "-H", f"User-Agent: {USER_AGENT}",
             "--max-time", "15"],
            capture_output=True, text=True, timeout=20
        )
        if p.returncode != 0:
            return []
        html_content = open("/tmp/ddg.html").read()
    except Exception as e:
        print(f"ERROR fetching DDG for '{query}': {e}", file=sys.stderr)
        return []

    # Check for challenge/blocked page
    if "blocked" in html_content.lower() or "challenge" in html_content.lower():
        return []

    results = []
    # DDG result links: <a rel="nofollow" class="result__a" href="...">...</a>
    pattern = r'<a rel="nofollow" class="result__a" href="([^"]+)">(.*?)</a>'
    for match in re.finditer(pattern, html_content, re.DOTALL):
        raw_url = match.group(1)
        raw_title = match.group(2)
        # Decode DDG redirect URL
        title_clean = re.sub(r'<[^>]+>', '', raw_title).strip()
        title_clean = html_mod.unescape(title_clean)
        
        # Extract real URL from DDG redirect
        m = re.search(r'uddg=([^&]+)', raw_url)
        if m:
            from urllib.parse import unquote
            real_url = unquote(m.group(1))
        else:
            real_url = raw_url
        
        if real_url and title_clean:
            results.append({"url": real_url, "title": title_clean})
        
        if len(results) >= limit:
            break
    
    return results

def classify(findings, competitor, query, title, desc, url):
    """Apply keyword→feature mapping heuristics."""
    title_lower = (title + desc).lower()
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
    
    return {
        "competitor": competitor,
        "query": query,
        "headline": title if title else url,
        "url": url,
        "announced_feature": feature_guess,
        "impact": impact_guess,
        "librebase_delta": f"Watch: {title}" if feature_guess else "",
        "raw_snippet": f"{title} — {desc[:300]}" if desc else title,
        "confidence": 0.65 if feature_guess else 0.45,
    }

# ── Watchlist ──
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

# ── Step 1: competitor searches ──
all_findings = []
seen_urls = set()
comp_limits = {c: 0 for c in COMPETITOR_QUERIES}

for comp, queries in COMPETITOR_QUERIES.items():
    for q in queries:
        results = ddg_search(q, limit=5)
        for r in results:
            url = r.get("url", "")
            if url in seen_urls:
                continue
            seen_urls.add(url)
            title = r.get("title", "")
            desc = ""
            
            finding = classify(all_findings, comp, q, title, desc, url)
            all_findings.append(finding)
            comp_limits[comp] = comp_limits.get(comp, 0) + 1
            
            if comp_limits[comp] >= 3:
                break
        if comp_limits[comp] >= 3:
            break

# ── Step 2: discovery searches ──
for q in DISCOVERY_QUERIES:
    results = ddg_search(q, limit=5)
    for r in results[:2]:
        url = r.get("url", "")
        if url in seen_urls:
            continue
        seen_urls.add(url)
        title = r.get("title", "")
        desc = ""
        
        is_agent = any(k in (title + desc).lower() for k in ["mcp", "agent", "agentic"])
        finding = {
            "competitor": "new",
            "competitor_url": url,
            "query": q,
            "headline": title if title else url,
            "url": url,
            "announced_feature": "mcp-agent-api" if is_agent else "",
            "impact": "new-competitor",
            "librebase_delta": "New competitor candidate — evaluate whether to track",
            "raw_snippet": f"{title} — {desc[:300]}" if desc else title,
            "confidence": 0.5,
            "disposition": "uncertain",
        }
        all_findings.append(finding)

# ── Step 3: persist ──
print(f"Collected {len(all_findings)} findings across {len(COMPETITOR_QUERIES)} competitors + {len(DISCOVERY_QUERIES)} discovery queries.", file=sys.stderr)

if all_findings:
    p = subprocess.run(
        [PYTHON, SCAN_CLI],
        input=json.dumps(all_findings),
        capture_output=True, text=True, cwd=DB_DIR
    )
    if p.returncode != 0:
        print(f"ERROR persisting (rc={p.returncode}): {p.stderr}", file=sys.stderr)
        sys.exit(1)
    persist_out = p.stdout.strip()
else:
    persist_out = "No findings generated today."

# ── Step 4: digest + status ──
for cmd in [["--digest"], ["--status"]]:
    p = subprocess.run([PYTHON, SCAN_CLI] + cmd, capture_output=True, text=True, cwd=DB_DIR)
    if p.returncode != 0:
        print(f"ERROR {cmd}: {p.stderr}", file=sys.stderr)

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
    f"Scanned {len(COMPETITOR_QUERIES)} known competitors + {len(DISCOVERY_QUERIES)} discovery queries. "
    "Confidence scores are coarse heuristics; treat as directional. "
    "Source: DuckDuckGo HTML (fallback mode)."
)

output = f"""
# LibreBase Competitive Intelligence — Daily Scan {today_str}

{note}

{digest}

---

## DB Status
{status}
"""

# Write digest file
digest_path = os.path.join(DB_DIR, f"competitive_digest_{today_str}.md")
with open(digest_path, "w") as f:
    f.write(output.strip() + "\n")

print(f"Digest file: {digest_path}")
print(f"Persisted: {persist_out}")
print()
print(output.strip())
