#!/usr/bin/env python3
"""
LibreBase Weekly Trend Scan — executed inside Hermes Agent runtime.

Imports hermes_tools (available only inside Hermes) to run the 8 trend queries,
classify findings against LibreBase's competitive positioning, persist to DB,
and write digest + strong-signal alert files.

Must be launched via: python3 weekly_trend_scan.py
from within the Hermes Agent Python environment (where hermes_tools is importable).
"""

import json
import os
import sqlite3
import subprocess
import sys
from datetime import date

# ── Paths ─────────────────────────────────────────────────────────────────────
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
LIBREBASE_DIR = os.path.expanduser("~/Documents/coding-projects/librebase")
SCAN_CLI = os.path.join(LIBREBASE_DIR, "librebase_competitive_scan.py")
DB_PATH = os.path.join(LIBREBASE_DIR, "librebase_competitive.db")
MARKETING_DIR = os.path.join(LIBREBASE_DIR, "data", "marketing")

os.environ["LIBREBASE_COMPETITIVE_DB"] = DB_PATH

# ── Import hermes tools (only available inside Hermes runtime) ───────────────
from hermes_tools import web_search, web_extract

# ── Trend queries ─────────────────────────────────────────────────────────────
# The 8 general BaaS/AI/cloud trend queries from daily_research.py
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

# ── Feature classification ────────────────────────────────────────────────────
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

STRONG_KEYWORDS = [
    "mcp", "agent api", "agent sdk", "agent skill", "model context protocol",
    "coding agent", "ai assistant", "cursor plugin",
    "vector", "embeddings", "pgvector",
    "edge function", "serverless function",
]

WEAK_KEYWORDS = [
    "self-host", "single binary", "open source", "docker compose",
    "lightweight", "simple", "easy", "minimal",
]


def classify(headline: str, url: str) -> tuple:
    """Return (feature_name, impact) for a search result."""
    text = (headline + " " + url).lower()

    matched_features = []
    for keyword, feature in FEATURE_MAP.items():
        if keyword in text:
            matched_features.append(feature)

    if not matched_features:
        if any(w in text for w in ["launch", "announce", "release", "introducing"]):
            return ("feature-launch", "neutral")
        return ("general", "noise")

    feature = matched_features[-1]

    is_strong = any(kw in text for kw in STRONG_KEYWORDS)
    is_weak = any(kw in text for kw in WEAK_KEYWORDS)

    if is_strong:
        return (feature, "strong")
    if is_weak:
        return (feature, "weak")
    return (feature, "neutral")


def is_duplicate(url: str, conn) -> bool:
    """Check if this URL was already scanned today."""
    row = conn.execute(
        "SELECT id FROM daily_scans WHERE url=? AND date(scanned_at)=date('now')",
        (url,),
    ).fetchone()
    return row is not None


def extract_content(url: str, top_results) -> str:
    """Extract content from the top result, falling back to snippet."""
    try:
        urls_to_extract = [url]
        for r in top_results[1:3]:
            u = r.get("url", "")
            if u and u != url:
                urls_to_extract.append(u)
                break
        result = web_extract(urls=urls_to_extract[:2], char_limit=3000)
        for r in result.get("results", []):
            if r.get("url") == url and not r.get("error"):
                content = r.get("content", "") or ""
                return content[:1500] if content else ""
    except Exception:
        pass
    return ""


def run():
    """Run the full trend scan."""

    # Ensure directories exist
    os.makedirs(MARKETING_DIR, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    print(f"[weekly-trend] LibreBase Weekly Trend Deep-Dive — {date.today().isoformat()}")
    print(f"[weekly-trend] DB: {DB_PATH}")
    print()

    total_findings = 0
    total_strong = 0
    all_findings = []

    for qi, query in enumerate(TREND_QUERIES, 1):
        print(f"[{qi}/8] Query: {query}")
        print("-" * 60)

        try:
            result = web_search(query, limit=5)
        except Exception as e:
            print(f"  ✗ search failed: {e}")
            continue

        results = result.get("data", {}).get("web", [])
        if not results:
            print("  → no results")
            continue

        query_findings = 0
        for r in results[:3]:
            url = r.get("url", "")
            title = r.get("title", "")
            snippet = r.get("description", "")

            if not url or not title:
                continue

            if is_duplicate(url, conn):
                continue

            feature, impact = classify(title, url)

            if impact == "noise":
                continue

            content = extract_content(url, results)

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
                "content_excerpt": content,
                "confidence": 0.65,
            }
            all_findings.append(finding)
            query_findings += 1
            total_findings += 1

            signal_icon = {"strong": "🔴", "weak": "🟢", "neutral": "⚪"}.get(impact, "·")
            print(f"  {signal_icon} [{impact:7s}] {feature:20s} | {title[:90]}")

        print(f"  → {query_findings} findings from this query")
        print()

    print("=" * 60)
    print(f"TOTAL: {total_findings} trend findings across {len(TREND_QUERIES)} queries")
    print()

    # ── Strong-signal alerts ──────────────────────────────────────────────────
    strong_findings = []
    for f in all_findings:
        if f["impact"] == "strong":
            strong_findings.append(f)

    if strong_findings:
        print(f"⚡ STRONG SIGNAL ALERTS ({len(strong_findings)})")
        print("-" * 60)
        alert_lines = []
        for sf in strong_findings[:20]:
            alert_lines.append(f"[{sf['competitor']}] {sf['headline']}")
            alert_lines.append(f"  Feature: {sf['announced_feature']} | Confidence: {sf['confidence']:.0%}")
            if sf["url"]:
                alert_lines.append(f"  URL: {sf['url']}")
            alert_lines.append(f"  Snippet: {sf['raw_snippet'][:200]}")
            alert_lines.append("")

        alert_text = "\n".join(alert_lines)
        print(alert_text)

        alerts_path = os.path.join(
            MARKETING_DIR, f"strong_alerts_{date.today().isoformat()}.md"
        )
        with open(alerts_path, "w") as fh:
            fh.write(f"# LibreBase Strong Signal Alerts — {date.today().isoformat()}\n\n")
            fh.write(f"**{len(strong_findings)} strong signals detected.**\n\n")
            fh.write(alert_text)
        print(f"→ alerts written: {alerts_path}")
        print()

    # ── Persist via scan CLI ──────────────────────────────────────────────────
    print("· Persisting to DB via librebase_competitive_scan.py ...")
    findings_json = json.dumps(all_findings)
    proc = subprocess.run(
        [sys.executable, SCAN_CLI],
        input=findings_json,
        capture_output=True,
        text=True,
        cwd=LIBREBASE_DIR,
    )
    if proc.returncode != 0:
        print(f"  ✗ scan CLI error: {proc.stderr}")
    else:
        stats = json.loads(proc.stdout)
        print(f"  ✓ persisted: {json.dumps(stats, indent=2)}")
        total_strong = stats.get("strong", 0)

    # ── Digest ────────────────────────────────────────────────────────────────
    print()
    print("· Generating digest ...")
    digest_proc = subprocess.run(
        [sys.executable, SCAN_CLI, "--digest"],
        capture_output=True,
        text=True,
        cwd=LIBREBASE_DIR,
    )
    if digest_proc.returncode == 0:
        digest_md = digest_proc.stdout
        digest_path = os.path.join(
            MARKETING_DIR, f"competitive_digest_{date.today().isoformat()}.md"
        )
        with open(digest_path, "w") as fh:
            fh.write(digest_md)
        print(f"  ✓ digest written: {digest_path}")
        print()
        print(digest_md)
    else:
        print(f"  ✗ digest failed: {digest_proc.stderr}")

    conn.close()

    return {
        "findings": total_findings,
        "strong_signals": total_strong,
        "queries_fired": len(TREND_QUERIES),
        "digest_file": os.path.join(
            MARKETING_DIR, f"competitive_digest_{date.today().isoformat()}.md"
        ),
        "alerts_file": os.path.join(
            MARKETING_DIR, f"strong_alerts_{date.today().isoformat()}.md"
        ) if strong_findings else None,
    }


if __name__ == "__main__":
    result = run()
    print()
    print("=" * 60)
    print(f"Done: {json.dumps(result, indent=2)}")
