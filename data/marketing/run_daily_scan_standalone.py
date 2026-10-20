#!/usr/bin/env python3
"""
Standalone LibreBase daily competitor scan runner.
Designed to be invoked via Hermes `execute_code` (which has hermes_tools).
Falls back gracefully when web tools are unavailable.
"""
import sys, os, json, subprocess, sqlite3
from datetime import date

LIBREBASE_DIR = os.path.expanduser("~/Documents/coding-projects/librebase")
SCAN_CLI = os.path.join(LIBREBASE_DIR, "librebase_competitive_scan.py")
DB_PATH = os.path.expanduser("~/Documents/coding-projects/librebase/librebase_competitive.db")
DIGEST_FILE = os.path.join(LIBREBASE_DIR, "data", "marketing",
                            f"competitive_digest_{date.today().isoformat()}.md")

# ── Import hermes_tools (only works inside Hermes runtime) ──
try:
    from hermes_tools import web_search, web_extract
    HERMES = True
except ImportError:
    HERMES = False
    web_search = None
    web_extract = None

if not HERMES:
    print("ERROR: This script must run inside Hermes execute_code (hermes_tools unavailable).")
    print("The cron job should invoke this via execute_code, not terminal.")
    sys.exit(1)

# ── Competitor queries ──
def competitor_queries(name, category):
    queries = [f"{name} new features OR announcement OR launch OR release 2026"]
    queries.append(f"{name} MCP server OR agent API OR AI SDK 2026")
    if category == "Other" or name in ("LoRA",):
        return queries
    if category in ("BaaS", "CMS-overlap"):
        queries.append(f"{name} pricing changes OR new plan OR free tier 2026")
    elif category == "AI-platform":
        queries.append(f"{name} model release OR API update OR agent 2026")
    elif category == "Cloud":
        queries.append(f"{name} serverless OR edge OR new region 2026")
    return queries

def trend_queries():
    return [
        "backend-as-a-service trends 2026 AI agents",
        "MCP server BaaS competitor wave 2026",
        "open source backend platform new features 2026",
        "serverless database edge compute developer tools 2026",
        "PostgreSQL managed service AI integration 2026",
        "real-time API backend platform comparison 2026",
        "developer tools AI agent SDK release 2026",
        "self-host Kubernetes BaaS alternative 2026",
    ]

FEATURE_MAP = {
    "mcp": "mcp-agent-api", "model context protocol": "mcp-agent-api",
    "agent api": "mcp-agent-api", "agent skill": "mcp-agent-api",
    "agent sdk": "mcp-agent-api", "coding agent": "mcp-agent-api",
    "ai assistant": "mcp-agent-api", "cursor plugin": "mcp-agent-api",
    "claude code": "mcp-agent-api", "opencode": "mcp-agent-api",
    "codex": "mcp-agent-api", "antigravity": "mcp-agent-api",
    "postgres": "postgresql-db", "postgresql": "postgresql-db",
    "sql": "postgresql-db", "database": "postgresql-db",
    "managed postgres": "postgresql-db",
    "pgvector": "vector-embeddings", "vector search": "vector-embeddings",
    "embedding": "vector-embeddings", "ai extension": "vector-embeddings",
    "auth": "auth", "authentication": "auth", "sign in": "auth",
    "sign-in": "auth", "login": "auth", "oauth": "auth", "sso": "auth",
    "mfa": "auth", "multi-factor": "auth",
    "storage": "storage", "file storage": "storage",
    "object storage": "storage", "blob": "storage",
    "realtime": "realtime", "websocket": "realtime",
    "subscription": "realtime", "live": "realtime", "broadcast": "realtime",
    "self-host": "self-host", "self host": "self-host",
    "docker compose": "self-host", "docker": "self-host",
    "single binary": "self-host", "single-file": "self-host",
    "kubernetes": "kubernetes", "k8s": "kubernetes", "helm": "kubernetes",
    "edge function": "edge-functions", "serverless function": "edge-functions",
    "cloud function": "edge-functions", "lambda": "edge-functions", "deno": "edge-functions",
    "graphql": "graphql", "rest api": "api-changes",
    "pricing": "pricing-changes", "price": "pricing-changes",
    "plan": "pricing-changes", "tier": "pricing-changes",
    "free tier": "pricing-changes", "pro plan": "pricing-changes", "cost": "pricing-changes",
    "funding": "funding", "series a": "funding", "series b": "funding",
    "raise": "funding", "acquisition": "funding", "acquired": "funding", "invest": "funding",
    "hiring": "hiring", "we're hiring": "hiring", "careers": "hiring",
    "job": "hiring", "engineering team": "hiring",
    "sdk": "sdk-release", "cli": "sdk-release", "client library": "sdk-release",
    "typescript": "sdk-release", "python": "sdk-release", "go sdk": "sdk-release",
    "documentation": "documentation", "docs": "documentation",
    "guide": "documentation", "tutorial": "documentation", "how to": "documentation",
    "enterprise": "enterprise-features", "rbac": "enterprise-features",
    "audit log": "enterprise-features", "sla": "enterprise-features",
    "compliance": "enterprise-features", "security": "enterprise-features",
    "open source": "open-source", "open-source": "open-source",
    "oss": "open-source", "mit": "open-source", "apache": "open-source", "bsd": "open-source",
    "console": "console-studio", "dashboard": "console-studio", "studio": "console-studio",
    "multi-region": "multi-region", "regional": "multi-region", "global": "multi-region",
    "custom domain": "custom-domains", "domain": "custom-domains",
    "delete": "delete-endpoints", "crud": "delete-endpoints", "lifecycle": "delete-endpoints",
    "billing": "billing-plans", "usage-based": "billing-metering",
    "metering": "billing-metering", "overages": "billing-metering",
    "newsletter": "go-to-market", "launch": "feature-launch",
    "release": "feature-launch", "beta": "feature-launch",
    "preview": "feature-launch", "generally available": "feature-launch",
    "ga": "feature-launch", "introducing": "feature-launch",
    "announcing": "feature-launch",
}

def classify_headline(headline, url):
    text = (headline + " " + url).lower()
    matched = []
    for kw, feat in FEATURE_MAP.items():
        if kw in text:
            matched.append(feat)
    if not matched:
        if any(w in text for w in ["launch", "announce", "release", "introducing"]):
            return ("feature-launch", "neutral")
        return ("general", "noise")
    feature = matched[-1]
    strong_signals = ["mcp", "agent api", "agent sdk", "agent skill",
                      "model context protocol", "coding agent", "ai assistant",
                      "cursor plugin", "vector", "embedding", "pgvector",
                      "edge function", "serverless function"]
    weak_signals = ["self-host", "single binary", "open source",
                    "docker compose", "lightweight", "simple", "easy"]
    if any(s in text for s in strong_signals):
        return (feature, "strong")
    if any(s in text for s in weak_signals):
        return (feature, "weak")
    return (feature, "neutral")

def already_scanned(conn, url):
    row = conn.execute(
        "SELECT id FROM daily_scans WHERE url=? AND date(scanned_at)=date('now')",
        (url,)
    ).fetchone()
    return row is not None

def run():
    total_queries = 0
    findings = []
    
    # Load competitors
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    comps = conn.execute(
        "SELECT id, name, url, category FROM competitors WHERE active=1 ORDER BY category, name"
    ).fetchall()
    positioning = {}
    for row in conn.execute("SELECT feature, strength, our_offer FROM our_positioning"):
        positioning[row["feature"]] = {"strength": row["strength"], "offer": row["our_offer"]}
    conn.close()
    
    print(f"[daily-research] Scope: all | Competitors: {len(comps)}")
    print()
    
    for comp in comps:
        name = comp["name"]
        comp_url = comp["url"]
        category = comp["category"]
        print(f"  [{category}] {name}")
        
        for query in competitor_queries(name, category):
            try:
                result = web_search(query, limit=5)
            except Exception as e:
                print(f"    ⚠ search failed: {e}")
                continue
            
            results = result.get("data", {}).get("web", [])
            if not results:
                continue
            
            for r in results[:3]:
                url = r.get("url", "")
                title = r.get("title", "")
                snippet = r.get("description", "")
                
                conn2 = sqlite3.connect(DB_PATH)
                conn2.row_factory = sqlite3.Row
                if already_scanned(conn2, url):
                    conn2.close()
                    continue
                conn2.close()
                
                feature, impact = classify_headline(title, url)
                
                # Content extraction
                extracted = ""
                if impact != "noise":
                    try:
                        urls_to_extract = [url]
                        for r2 in results[1:3]:
                            u2 = r2.get("url", "")
                            if u2 and u2 != url:
                                urls_to_extract.append(u2)
                                break
                        extract_result = web_extract(urls=urls_to_extract[:2], char_limit=3000)
                        for res in extract_result.get("results", []):
                            if res.get("url") == url and not res.get("error"):
                                extracted = res.get("content", "") or ""
                                break
                    except Exception:
                        extracted = snippet
                
                # delta text
                delta = ""
                if feature in positioning and impact == "strong":
                    strength = positioning[feature]["strength"]
                    if strength == "weak":
                        delta = f"LibreBase is WEAK on {feature}; competitor is gaining ground here"
                    elif strength == "neutral":
                        delta = f"LibreBase NEUTRAL on {feature}; competitor is now strong — monitor"
                    else:
                        delta = f"LibreBase strong on {feature} but competitor is adding it — competitive pressure"
                
                conf = 0.75
                if impact == "strong":
                    content_check = (extracted or snippet).lower()
                    if any(k in content_check for k in ["mcp", "agent", "launch", "announce", "introducing", "new"]):
                        conf = min(0.85, conf + 0.1)
                
                if impact != "noise":
                    finding = {
                        "competitor": name,
                        "competitor_url": comp_url or "",
                        "query": query,
                        "headline": title[:200],
                        "url": url,
                        "announced_feature": feature,
                        "impact": impact,
                        "librebase_delta": delta,
                        "raw_snippet": snippet[:500],
                        "content_excerpt": extracted[:1500] if extracted else snippet[:500],
                        "confidence": conf,
                    }
                    findings.append(finding)
                    total_queries += 1
        
        comp_findings = len([f for f in findings if f['competitor'] == name])
        print(f"    → {comp_findings} findings")
    
    # Trend scans
    print(f"\n  [trends] General BaaS/AI/cloud trend scan")
    for query in trend_queries():
        try:
            result = web_search(query, limit=3)
        except Exception as e:
            print(f"    ⚠ trend search failed: {e}")
            continue
        
        results = result.get("data", {}).get("web", [])
        for r in results:
            url = r.get("url", "")
            title = r.get("title", "")
            snippet = r.get("description", "")
            
            conn2 = sqlite3.connect(DB_PATH)
            conn2.row_factory = sqlite3.Row
            if already_scanned(conn2, url):
                conn2.close()
                continue
            conn2.close()
            
            feature, impact = classify_headline(title, url)
            if impact == "noise":
                continue
            
            extracted = ""
            try:
                urls_to_extract = [url]
                for r2 in results[1:3]:
                    u2 = r2.get("url", "")
                    if u2 and u2 != url:
                        urls_to_extract.append(u2)
                        break
                extract_result = web_extract(urls=urls_to_extract[:2], char_limit=2000)
                for res in extract_result.get("results", []):
                    if res.get("url") == url and not res.get("error"):
                        extracted = res.get("content", "") or ""
                        break
            except Exception:
                extracted = snippet
            
            finding = {
                "competitor": "General trend" if impact != "new-competitor" else "new",
                "competitor_url": url,
                "query": query,
                "headline": title[:200],
                "url": url,
                "announced_feature": feature,
                "impact": impact,
                "librebase_delta": "",
                "raw_snippet": snippet[:500],
                "content_excerpt": extracted[:1000] if extracted else snippet[:500],
                "confidence": 0.65,
            }
            findings.append(finding)
            total_queries += 1
    
    print(f"\n  Total findings: {len(findings)}")
    print(f"  Total queries fired: {total_queries}")
    
    # Strong-signal alerts
    strong = [f for f in findings if f["impact"] == "strong"]
    if strong:
        print(f"\n  ⚡ STRONG SIGNAL ALERTS ({len(strong)} findings)")
        print(f"  ─────────────────────────────────────────────")
        for sf in strong[:20]:
            print(f"  [{sf['competitor']}] {sf['headline']}")
            print(f"    Feature: {sf['announced_feature']} | Confidence: {sf['confidence']:.0%}")
            if sf['url']:
                print(f"    URL: {sf['url']}")
            if sf['librebase_delta']:
                print(f"    Delta: {sf['librebase_delta']}")
            print()
    
    # Persist
    print("\n  Persisting findings...")
    findings_json = json.dumps(findings)
    proc = subprocess.run(
        [sys.executable, SCAN_CLI],
        input=findings_json,
        capture_output=True, text=True,
        cwd=LIBREBASE_DIR,
    )
    if proc.returncode != 0:
        print(f"  ⚠ scan CLI error: {proc.stderr}")
    else:
        stats = json.loads(proc.stdout)
        print(f"  ✓ persisted: {json.dumps(stats, indent=2)}")
    
    # Digest
    digest_proc = subprocess.run(
        [sys.executable, SCAN_CLI, "--digest"],
        capture_output=True, text=True,
        cwd=LIBREBASE_DIR,
    )
    if digest_proc.returncode == 0:
        digest_md = digest_proc.stdout
        os.makedirs(os.path.dirname(DIGEST_FILE), exist_ok=True)
        with open(DIGEST_FILE, "w") as fh:
            fh.write(digest_md)
        print(f"  ✓ digest written: {DIGEST_FILE}")
    
    print("\n" + "=" * 70)
    print(digest_proc.stdout)
    
    return {
        "findings": len(findings),
        "strong_count": len(strong),
        "queries": total_queries,
        "digest_file": DIGEST_FILE,
    }

if __name__ == "__main__":
    result = run()
    print(f"\nDone: {json.dumps(result, indent=2)}")
