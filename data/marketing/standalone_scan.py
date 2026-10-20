#!/usr/bin/env python3
"""
LibreBase Daily Competitor Scan — standalone runner.
Uses web_search + web_extract tool calls directly (not via hermes_tools import),
then pipes findings to librebase_competitive_scan.py for persistence.
Works in cron (system Python) contexts where hermes_tools isn't importable.
"""

import json
import os
import subprocess
import sys
from datetime import date

LIBREBASE_DIR = os.path.expanduser("~/Documents/coding-projects/librebase")
SCAN_CLI = os.path.join(LIBREBASE_DIR, "librebase_competitive_scan.py")
DB = os.path.join(LIBREBASE_DIR, "librebase_competitive.db")
DIGEST_FILE = os.path.join(LIBREBASE_DIR, "data", "marketing",
                        f"competitive_digest_{date.today().isoformat()}.md")

# Competitor list from DB (34 active competitors)
COMPETITORS = [
    # AI-platform
    ("Anthropic", "https://anthropic.com", "AI-platform"),
    ("Baseten", "https://baseten.com", "AI-platform"),
    ("ElevenLabs", "https://elevenlabs.io", "AI-platform"),
    ("Harper", "https://www.harper.fast/resources/your-applications-mcp-native", "AI-platform"),
    ("HuggingFace", "https://huggingface.co", "AI-platform"),
    ("LangChain", "https://python.langchain.com", "AI-platform"),
    ("LoRA", "https://lora.company", "AI-platform"),
    ("OpenAI Agents", "https://platform.openai.com", "AI-platform"),
    # BaaS
    ("AWS Amplify", "https://aws.amazon.com/amplify/", "BaaS"),
    ("Appwrite", "https://appwrite.io", "BaaS"),
    ("Azure Static Web Apps", "https://azure.microsoft.com/en-us/services/app-service/static/", "BaaS"),
    ("Convex", "https://convex.dev", "BaaS"),
    ("Firebase", "https://firebase.google.com", "BaaS"),
    ("Knack", "https://www.prnewswire.com/news-releases/knack-launches-mcp-server-the-hipaa-compliant-backend-for-ai-builders-302860109.html", "BaaS"),
    ("Koywe", "https://koywe.com", "BaaS"),
    ("Merge.dev", "https://merge.dev", "BaaS"),
    ("Nango", "https://getsoku.com", "BaaS"),
    ("Neon", "https://neon.tech", "BaaS"),
    ("Nhost", "https://nhost.io", "BaaS"),
    ("PocketBase", "https://pocketbase.io", "BaaS"),
    ("Retool", "https://retool.com", "BaaS"),
    ("Supabase", "https://supabase.com", "BaaS"),
    ("Xano", "https://xano.com", "BaaS"),
    ("backenly", "https://github.com/backenly/backenly", "BaaS"),
    # Backend
    ("ElectricSQL", "https://electric-sql.com", "Backend"),
    ("Sequin", "https://sequin.io", "Backend"),
    # CMS-overlap
    ("Directus", "https://directus.io", "CMS-overlap"),
    # Cloud
    ("Cloudflare Workers", "https://developers.cloudflare.com", "Cloud"),
    ("Vercel", "https://vercel.com", "Cloud"),
    # Other
    ("PowerDNS", "", "Other"),
    # PaaS
    ("Fly.io", "https://fly.io", "PaaS"),
    ("Heroku", "https://www.heroku.com", "PaaS"),
    ("Railway", "https://railway.app", "PaaS"),
    ("Render", "https://render.com", "PaaS"),
]

# Feature classification map (same as daily_research.py)
FEATURE_MAP = {
    "mcp": "mcp-agent-api",
    "model context protocol": "mcp-agent-api",
    "agent api": "mcp-agent-api",
    "agent skill": "mcp-agent-api",
    "agent sdk": "mcp-agent-api",
    "coding agent": "mcp-agent-api",
    "ai assistant": "mcp-agent-api",
    "cursor plugin": "mcp-agent-api",
    "claude code": "mcp-agent-api",
    "opencode": "mcp-agent-api",
    "codex": "mcp-agent-api",
    "antigravity": "mcp-agent-api",
    "postgres": "postgresql-db",
    "postgresql": "postgresql-db",
    "sql": "postgresql-db",
    "database": "postgresql-db",
    "managed postgres": "postgresql-db",
    "pgvector": "vector-embeddings",
    "vector search": "vector-embeddings",
    "embedding": "vector-embeddings",
    "ai extension": "vector-embeddings",
    "auth": "auth",
    "authentication": "auth",
    "sign in": "auth",
    "sign-in": "auth",
    "login": "auth",
    "oauth": "auth",
    "sso": "auth",
    "mfa": "auth",
    "multi-factor": "auth",
    "storage": "storage",
    "file storage": "storage",
    "object storage": "storage",
    "blob": "storage",
    "realtime": "realtime",
    "websocket": "realtime",
    "subscription": "realtime",
    "live": "realtime",
    "broadcast": "realtime",
    "self-host": "self-host",
    "self host": "self-host",
    "docker compose": "self-host",
    "docker": "self-host",
    "single binary": "self-host",
    "single-file": "self-host",
    "kubernetes": "kubernetes",
    "k8s": "kubernetes",
    "helm": "kubernetes",
    "edge function": "edge-functions",
    "serverless function": "edge-functions",
    "cloud function": "edge-functions",
    "lambda": "edge-functions",
    "deno": "edge-functions",
    "graphql": "graphql",
    "rest api": "api-changes",
    "pricing": "pricing-changes",
    "price": "pricing-changes",
    "plan": "pricing-changes",
    "tier": "pricing-changes",
    "free tier": "pricing-changes",
    "pro plan": "pricing-changes",
    "cost": "pricing-changes",
    "funding": "funding",
    "series a": "funding",
    "series b": "funding",
    "raise": "funding",
    "acquisition": "funding",
    "acquired": "funding",
    "invest": "funding",
    "hiring": "hiring",
    "we're hiring": "hiring",
    "careers": "hiring",
    "job": "hiring",
    "engineering team": "hiring",
    "sdk": "sdk-release",
    "cli": "sdk-release",
    "client library": "sdk-release",
    "typescript": "sdk-release",
    "python": "sdk-release",
    "go sdk": "sdk-release",
    "documentation": "documentation",
    "docs": "documentation",
    "guide": "documentation",
    "tutorial": "documentation",
    "how to": "documentation",
    "enterprise": "enterprise-features",
    "rbac": "enterprise-features",
    "audit log": "enterprise-features",
    "sla": "enterprise-features",
    "compliance": "enterprise-features",
    "security": "enterprise-features",
    "open source": "open-source",
    "open-source": "open-source",
    "oss": "open-source",
    "mit": "open-source",
    "apache": "open-source",
    "bsd": "open-source",
    "console": "console-studio",
    "dashboard": "console-studio",
    "studio": "console-studio",
    "multi-region": "multi-region",
    "regional": "multi-region",
    "global": "multi-region",
    "custom domain": "custom-domains",
    "domain": "custom-domains",
    "delete": "delete-endpoints",
    "crud": "delete-endpoints",
    "lifecycle": "delete-endpoints",
    "billing": "billing-plans",
    "usage-based": "billing-metering",
    "metering": "billing-metering",
    "overages": "billing-metering",
    "newsletter": "go-to-market",
    "launch": "feature-launch",
    "release": "feature-launch",
    "beta": "feature-launch",
    "preview": "feature-launch",
    "generally available": "feature-launch",
    "ga": "feature-launch",
    "introducing": "feature-launch",
    "announcing": "feature-launch",
}

STRONG_SIGNALS = [
    "mcp", "agent api", "agent sdk", "agent skill", "model context protocol",
    "coding agent", "ai assistant", "cursor plugin",
    "vector", "embedding", "pgvector",
    "edge function", "serverless function",
]

WEAK_SIGNALS = [
    "self-host", "single binary", "open source", "docker compose",
    "lightweight", "simple", "easy",
]

TREND_QUERIES = [
    "backend-as-a-service trends 2026 AI agents",
    "MCP server BaaS competitor wave 2026",
    "open source backend platform new features 2026",
    "serverless database edge compute developer tools 2026",
    "PostgreSQL managed service AI integration 2026",
    "real-time API backend platform comparison 2026",
    "developer tools AI agent SDK release 2026",
    "self-host Kubernetes BaaS alternative 2026",
]


def classify_headline(headline: str, url: str) -> tuple:
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
    is_strong = any(s in text for s in STRONG_SIGNALS)
    is_weak = any(s in text for s in WEAK_SIGNALS)
    if is_strong:
        return (feature, "strong")
    if is_weak:
        return (feature, "weak")
    return (feature, "neutral")


def build_competitor_queries(name: str, category: str):
    queries = [f"{name} new features OR announcement OR launch OR release 2026"]
    queries.append(f"{name} MCP server OR agent API OR AI SDK 2026")
    if category == "Other" or name == "LoRA":
        return queries
    if category in ("BaaS", "CMS-overlap"):
        queries.append(f"{name} pricing changes OR new plan OR free tier 2026")
    elif category == "AI-platform":
        queries.append(f"{name} model release OR API update OR agent 2026")
    elif category == "Cloud":
        queries.append(f"{name} serverless OR edge OR new region 2026")
    return queries


def query_db_seen_urls():
    """Return set of URLs already scanned today."""
    try:
        import sqlite3
        conn = sqlite3.connect(DB)
        rows = conn.execute(
            "SELECT url FROM daily_scans WHERE date(scanned_at)=date('now')"
        ).fetchall()
        conn.close()
        return {r[0] for r in rows if r[0]}
    except Exception:
        return set()


def run():
    print(f"[standalone-scan] Scope: all | Competitors: {len(COMPETITORS)}")
    print(f"[standalone-scan] Date: {date.today().isoformat()}")
    print()

    seen_urls = query_db_seen_urls()
    findings = []
    total_queries = 0

    for name, url, category in COMPETITORS:
        print(f"  [{category}] {name}")
        queries = build_competitor_queries(name, category)

        for qi, query in enumerate(queries):
            try:
                from hermes_tools import web_search
                result = web_search(query, limit=5)
                results = result.get("data", {}).get("web", [])
            except ImportError:
                # Fallback: can't search, skip
                print(f"    ⚠ web_search not available (ImportError) — skipping query #{qi+1}")
                continue
            except Exception as e:
                print(f"    ⚠ search #{qi+1} failed: {e}")
                continue

            if not results:
                continue

            for r in results[:3]:
                url_found = r.get("url", "")
                title = r.get("title", "")
                snippet = r.get("description", "")

                if url_found in seen_urls:
                    continue

                feature, impact = classify_headline(title, url_found)
                if impact == "noise":
                    continue

                # Content extraction for top result
                extracted_content = snippet
                try:
                    from hermes_tools import web_extract
                    urls_to_extract = [url_found]
                    for r2 in results[1:3]:
                        u2 = r2.get("url", "")
                        if u2 and u2 != url_found:
                            urls_to_extract.append(u2)
                            break
                    ext_result = web_extract(urls=urls_to_extract[:2], char_limit=3000)
                    for res in ext_result.get("results", []):
                        if res.get("url") == url_found and not res.get("error"):
                            extracted_content = res.get("content", "") or snippet
                            break
                except ImportError:
                    pass
                except Exception:
                    pass

                # Build librebase_delta
                delta_text = ""
                if impact == "strong":
                    delta_text = f"LibreBase is WEAK on {feature}; competitor is gaining ground here"
                elif impact == "weak":
                    delta_text = f"Competitor weak on {feature}; LibreBase position stable"
                else:
                    delta_text = f"Tracking {feature} evolution for {name}"

                # Confidence
                conf = 0.75
                content_lower = (extracted_content or snippet).lower()
                if impact == "strong" and any(k in content_lower for k in ["mcp", "agent", "launch", "announce", "introducing", "new"]):
                    conf += 0.1
                elif impact == "weak" and any(k in content_lower for k in ["self-host", "open source", "simple", "lightweight"]):
                    conf += 0.1
                conf = min(conf, 0.95)

                finding = {
                    "competitor": name,
                    "competitor_url": url or "",
                    "query": query,
                    "headline": title[:200],
                    "url": url_found,
                    "announced_feature": feature,
                    "impact": impact,
                    "librebase_delta": delta_text,
                    "raw_snippet": snippet[:500],
                    "content_excerpt": (extracted_content or snippet)[:1500],
                    "confidence": conf,
                }
                findings.append(finding)
                seen_urls.add(url_found)
                total_queries += 1

        per_comp = len([f for f in findings if f["competitor"] == name])
        print(f"    → {per_comp} findings")
        # Throttle between competitors to avoid rate limits
        import time
        time.sleep(1)

    # Trend scans
    print(f"\n  [trends] General BaaS/AI/cloud trend scan")
    for query in TREND_QUERIES:
        try:
            from hermes_tools import web_search
            result = web_search(query, limit=3)
            results = result.get("data", {}).get("web", [])
        except ImportError:
            print(f"    ⚠ web_search not available — skipping trend query")
            continue
        except Exception as e:
            print(f"    ⚠ trend search failed: {e}")
            continue

        for r in results:
            url_found = r.get("url", "")
            title = r.get("title", "")
            snippet = r.get("description", "")

            if url_found in seen_urls:
                continue

            feature, impact = classify_headline(title, url_found)
            if impact == "noise":
                continue

            extracted_content = snippet
            try:
                from hermes_tools import web_extract
                urls_to_extract = [url_found]
                for r2 in results[1:3]:
                    u2 = r2.get("url", "")
                    if u2 and u2 != url_found:
                        urls_to_extract.append(u2)
                        break
                ext_result = web_extract(urls=urls_to_extract[:2], char_limit=2000)
                for res in ext_result.get("results", []):
                    if res.get("url") == url_found and not res.get("error"):
                        extracted_content = res.get("content", "") or snippet
                        break
            except ImportError:
                pass
            except Exception:
                pass

            finding = {
                "competitor": "General trend" if impact != "new-competitor" else "new",
                "competitor_url": url_found,
                "query": query,
                "headline": title[:200],
                "url": url_found,
                "announced_feature": feature,
                "impact": impact,
                "librebase_delta": "",
                "raw_snippet": snippet[:500],
                "content_excerpt": (extracted_content or snippet)[:1000],
                "confidence": 0.65,
            }
            findings.append(finding)
            seen_urls.add(url_found)
            total_queries += 1

        import time
        time.sleep(1)

    print(f"\n  Total findings: {len(findings)}")
    print(f"  Total queries fired: {total_queries}")
    print()

    # Strong-signal alerts
    strong = [f for f in findings if f["impact"] == "strong"]
    if strong:
        print(f"  ⚡ STRONG SIGNAL ALERTS ({len(strong)} findings)")
        print(f"  ─────────────────────────────────────────────")
        for sf in strong[:20]:
            print(f"  [{sf['competitor']}] {sf['headline']}")
            print(f"    Feature: {sf['announced_feature']} | Confidence: {sf['confidence']:.0%}")
            if sf['url']:
                print(f"    URL: {sf['url']}")
            if sf['librebase_delta']:
                print(f"    Delta: {sf['librebase_delta']}")
            print()

        alerts_path = os.path.join(LIBREBASE_DIR, "data", "marketing",
                                   f"strong_alerts_{date.today().isoformat()}.md")
        os.makedirs(os.path.dirname(alerts_path), exist_ok=True)
        with open(alerts_path, "w") as fh:
            fh.write(f"# LibreBase Strong Signal Alerts — {date.today().isoformat()}\n\n")
            fh.write(f"**{len(strong)} strong signals detected.**\n\n")
            for sf in strong[:20]:
                fh.write(f"[{sf['competitor']}] {sf['headline']}\n")
                fh.write(f"  Feature: {sf['announced_feature']} | Confidence: {sf['confidence']:.0%}\n")
                if sf['url']:
                    fh.write(f"  URL: {sf['url']}\n")
                if sf['librebase_delta']:
                    fh.write(f"  Delta: {sf['librebase_delta']}\n")
                fh.write("\n")
        print(f"  → alerts written: {alerts_path}")
        print()

    # Persist
    if findings:
        print("  Persisting findings...")
        findings_json = json.dumps(findings)
        proc = subprocess.run(
            [sys.executable, SCAN_CLI],
            input=findings_json,
            capture_output=True,
            text=True,
            cwd=LIBREBASE_DIR,
        )
        if proc.returncode != 0:
            print(f"  ⚠ scan CLI error: {proc.stderr}")
        else:
            stats = json.loads(proc.stdout)
            print(f"  ✓ persisted: {json.dumps(stats, indent=2)}")

        # Write digest
        digest_proc = subprocess.run(
            [sys.executable, SCAN_CLI, "--digest"],
            capture_output=True,
            text=True,
            cwd=LIBREBASE_DIR,
        )
        if digest_proc.returncode == 0:
            os.makedirs(os.path.dirname(DIGEST_FILE), exist_ok=True)
            with open(DIGEST_FILE, "w") as fh:
                fh.write(digest_proc.stdout)
            print(f"  ✓ digest written: {DIGEST_FILE}")
    else:
        print("  No findings to persist.")

    # Print digest
    digest_proc = subprocess.run(
        [sys.executable, SCAN_CLI, "--digest"],
        capture_output=True,
        text=True,
        cwd=LIBREBASE_DIR,
    )
    if digest_proc.returncode == 0:
        print("\n" + "=" * 70)
        print(digest_proc.stdout)

    strong_count = len([f for f in findings if f["impact"] == "strong"])
    return {
        "findings": len(findings),
        "queries": total_queries,
        "strong": strong_count,
        "digest_file": DIGEST_FILE,
    }


if __name__ == "__main__":
    result = run()
    print(f"\nDone: {json.dumps(result, indent=2)}")
