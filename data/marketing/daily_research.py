#!/usr/bin/env python3
"""
Unified LibreBase Daily Competitor Research Script.

Runs on top of librebase_competitive.db (the canonical competitive DB).
Scans all 31 competitors across 5 categories + general BaaS/AI/cloud trends,
extracts findings via web_search/web_extract, and pipes them to
librebase_competitive_scan.py for persistence.

Usage:
  python3 daily_research.py [--scope all|baas|cloud|ai-platform|paaS|backend|cms-overlap]
  python3 daily_research.py --dry-run          # show queries only, don't run

Output:
  - DB rows in daily_scans (append-only)
  - Feature changes tracked in competitor_feature_history
  - Digest printed to stdout
  - Optional: competitive_digest_YYYY-MM-DD.md

Cron target: weekdays 04:30 CEST (02:30 UTC)
"""

import argparse
import json
import os
import re
import sys
import subprocess
from datetime import date, datetime, timezone
from typing import List, Dict, Any

# ── Paths ────────────────────────────────────────────────────────────────────
LIBREBASE_DIR = os.path.expanduser("~/Documents/coding-projects/librebase")
SCAN_CLI = os.path.join(LIBREBASE_DIR, "librebase_competitive_scan.py")
DIGEST_FILE = os.path.join(
    LIBREBASE_DIR, "data", "marketing",
    f"competitive_digest_{date.today().isoformat()}.md"
)

# ── Web tools ────────────────────────────────────────────────────────────────
# These are only available inside the Hermes agent runtime.
# When running via cron (system Python), this script is called from a wrapper
# that runs inside Hermes execute_code, where hermes_tools is available.
try:
    from hermes_tools import web_search, web_extract
    _HERMES_RUNTIME = True
except ImportError:
    _HERMES_RUNTIME = False
    web_search = None
    web_extract = None


# ── Competitor query templates ───────────────────────────────────────────────
def competitor_queries(name: str, category: str) -> List[str]:
    """Generate search queries for a single competitor.

    Each competitor gets 3 queries:
      1. New features/announcements (broad)
      2. MCP/agent/AI-specific (targeted — this is where the competitive action is)
      3. Pricing/business (neutral coverage)
    """
    queries = [
        f"{name} new features OR announcement OR launch OR release 2026",
    ]
    # Targeted MCP/agent query for all competitors (this is where the competitive action is)
    queries.append(f"{name} MCP server OR agent API OR AI SDK 2026")

    # Watch-list competitors: 1 query only (broad coverage, no pricing/MCP deep-dive)
    if category == "Other" or name in ("LoRA",):
        return queries

    if category in ("BaaS", "CMS-overlap"):
        queries.append(f"{name} pricing changes OR new plan OR free tier 2026")
    elif category == "AI-platform":
        queries.append(f"{name} model release OR API update OR agent 2026")
    elif category == "Cloud":
        queries.append(f"{name} serverless OR edge OR new region 2026")

    return queries


def trend_queries() -> List[str]:
    """General BaaS / AI / cloud trend queries (run once per day)."""
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


# ── Finding classification ───────────────────────────────────────────────────
FEATURE_MAP: Dict[str, str] = {
    # Keywords → LibreBase feature name (from our_positioning table)
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


def classify_headline(headline: str, url: str) -> tuple[str, str]:
    """Return (announced_feature, impact) for a finding.

    impact: 'strong' (competitor strong on a LibreBase-weak feature),
            'weak' (competitor weak — LibreBase strong),
            'neutral' (comparable/tracking),
            'new-competitor' (new entrant),
            'noise' (not material).
    """
    text = (headline + " " + url).lower()

    # Determine which feature this touches
    matched_features = []
    for keyword, feature in FEATURE_MAP.items():
        if keyword in text:
            matched_features.append(feature)

    if not matched_features:
        # Not matching any known LibreBase feature — classify as neutral noise
        # unless it's clearly an announcement
        if any(w in text for w in ["launch", "announce", "release", "introducing"]):
            return ("feature-launch", "neutral")
        return ("general", "noise")

    # Pick the most specific feature (longest match first)
    feature = matched_features[-1]  # last match usually more specific

    # Determine impact
    # Strong: competitor adding MCP/agent/AI features (LibreBase weak areas being attacked)
    strong_signals = [
        "mcp", "agent api", "agent sdk", "agent skill", "model context protocol",
        "coding agent", "ai assistant", "cursor plugin",
        "vector", "embedding", "pgvector",
        "edge function", "serverless function",
    ]
    weak_signals = [
        "self-host", "single binary", "open source", "docker compose",
        "lightweight", "simple", "easy",
    ]

    is_strong = any(s in text for s in strong_signals)
    is_weak = any(s in text for s in weak_signals)

    if is_strong:
        return (feature, "strong")
    if is_weak:
        return (feature, "weak")
    return (feature, "neutral")


# ── Main scan loop ───────────────────────────────────────────────────────────
def run_daily_scan(scope: str = "all", dry_run: bool = False) -> Dict[str, Any]:
    """Run the full daily scan and return stats."""
    categories = {
        "all": None,
        "baas": "BaaS",
        "cloud": "Cloud",
        "ai-platform": "AI-platform",
        "paas": "PaaS",
        "backend": "Backend",
        "cms-overlap": "CMS-overlap",
    }
    # ── Paths (needed for all scopes) ────────────────────────────────────────
    DB = os.environ.get(
        "LIBREBASE_COMPETITIVE_DB",
        os.path.expanduser("~/Documents/coding-projects/librebase/librebase_competitive.db"),
    )

    # Special case: trends-only — return early with just trend queries
    if scope == "trends-only":
        print(f"[daily-research] Scope: trends-only | (no per-competitor scanning)")
        print()
        total_queries = 0
        findings = []

        print(f"  [trends] General BaaS/AI/cloud trend deep-dive")
        for query in trend_queries():
            if dry_run:
                print(f"    [DRY] trend query: {query}")
                total_queries += 1
                continue

            try:
                result = web_search(query, limit=5)
            except Exception as e:
                print(f"    ⚠ trend search failed: {e}")
                continue

            results = result.get("data", {}).get("web", [])
            if not results:
                continue

            for r in results[:3]:
                url = r.get("url", "")
                title = r.get("title", "")
                snippet = r.get("description", "")

                # Dedupe against today's scans (local db check)
                import sqlite3 as _sq2
                _c2 = _sq2.connect(DB)
                _c2.row_factory = _sq2.Row
                existing = _c2.execute(
                    "SELECT id FROM daily_scans WHERE url=? AND date(scanned_at)=date('now')",
                    (url,),
                ).fetchone()
                _c2.close()
                if existing:
                    continue

                feature, impact = classify_headline(title, url)
                if impact == "noise":
                    continue

                # Content extraction
                extracted_content = ""
                if not _HERMES_RUNTIME and web_extract is None:
                    extracted_content = snippet
                else:
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
                                extracted_content = res.get("content", "") or ""
                                break
                    except Exception:
                        extracted_content = snippet

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
                    "content_excerpt": extracted_content[:1000] if extracted_content else snippet[:500],
                    "confidence": 0.65,
                }
                findings.append(finding)
                total_queries += 1

        print(f"    → {len(findings)} trend findings")

        print(f"\n  Total findings: {len(findings)}")
        print(f"  Total queries fired: {total_queries}")

        if dry_run:
            print("\n[DRY RUN] No data persisted. Rerun without --dry-run to execute.")
            return {"findings": len(findings), "queries": total_queries, "dry_run": True}

        # ── Strong-signal alerts ──────────────────────────────────────────────
        strong_findings = [f for f in findings if f["impact"] == "strong"]
        if strong_findings:
            print(f"\n  ⚡ STRONG SIGNAL ALERTS ({len(strong_findings)} findings)")
            print(f"  ─────────────────────────────────────────────")
            alert_lines = []
            for sf in strong_findings[:20]:
                delta = sf.get("librebase_delta", "")
                fname = sf.get("announced_feature", "unknown")
                competitor = sf.get("competitor", "unknown")
                headline = sf.get("headline", "")
                url = sf.get("url", "")
                conf = sf.get("confidence", 0.75)
                alert_lines.append(f"  [{competitor}] {headline}")
                alert_lines.append(f"    Feature: {fname} | Confidence: {conf:.0%}")
                if url:
                    alert_lines.append(f"    URL: {url}")
                if delta:
                    alert_lines.append(f"    Delta: {delta}")
                alert_lines.append("")
            alert_text = "\n".join(alert_lines)
            print(alert_text)
            alerts_path = os.path.join(
                LIBREBASE_DIR, "data", "marketing",
                f"strong_alerts_{date.today().isoformat()}.md"
            )
            with open(alerts_path, "w") as fh:
                fh.write(f"# LibreBase Strong Signal Alerts — {date.today().isoformat()}\n\n")
                fh.write(f"**{len(strong_findings)} strong signals detected.**\n\n")
                fh.write(alert_text)
            print(f"  → alerts written: {alerts_path}")

        # ── Persist via scan CLI ──────────────────────────────────────────────
        print("\n  Persisting findings...")
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

        digest_proc = subprocess.run(
            [sys.executable, SCAN_CLI, "--digest"],
            capture_output=True,
            text=True,
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
            "queries": total_queries,
            "digest_file": DIGEST_FILE,
        }

    # Resolve category filter from scope
    filter_cat = categories.get(scope)

    # ── Load competitors from DB ──────────────────────────────────────────────
    import sqlite3
    DB = os.environ.get(
        "LIBREBASE_COMPETITIVE_DB",
        os.path.expanduser("~/Documents/coding-projects/librebase/librebase_competitive.db"),
    )
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    if filter_cat:
        comps = conn.execute(
            "SELECT id, name, url, category FROM competitors WHERE category=? AND active=1 ORDER BY name",
            (filter_cat,),
        ).fetchall()
    else:
        comps = conn.execute(
            "SELECT id, name, url, category FROM competitors WHERE active=1 ORDER BY category, name"
        ).fetchall()

    # Also load our positioning for the librebase_delta field
    positioning = {}
    for row in conn.execute("SELECT feature, strength, our_offer FROM our_positioning"):
        positioning[row["feature"]] = {
            "strength": row["strength"],
            "offer": row["our_offer"],
        }
    conn.close()

    total_queries = 0
    findings = []
    new_competitor_candidates = []

    print(f"[daily-research] Scope: {scope} | Competitors: {len(comps)}")
    print()

    for comp in comps:
        name = comp["name"]
        comp_url = comp["url"]
        category = comp["category"]

        print(f"  [{category}] {name}")

        for qi, query in enumerate(competitor_queries(name, category)):
            if dry_run:
                print(f"    [DRY] query #{qi+1}: {query}")
                total_queries += 1
                continue

            try:
                result = web_search(query, limit=5)
            except Exception as e:
                print(f"    ⚠ search #{qi+1} failed: {e}")
                continue

            results = result.get("data", {}).get("web", [])
            if not results:
                continue

            for r in results[:3]:  # cap at 3 per query per competitor
                url = r.get("url", "")
                title = r.get("title", "")
                snippet = r.get("description", "")

                # Dedupe against today's scans
                import sqlite3 as sq2
                c2 = sq2.connect(DB)
                c2.row_factory = sq2.Row
                existing = c2.execute(
                    "SELECT id FROM daily_scans WHERE url=? AND date(scanned_at)=date('now')",
                    (url,),
                ).fetchone()
                c2.close()
                if existing:
                    continue

                feature, impact = classify_headline(title, url)

                # ── Content extraction: upgrade from snippet to full page text ──
                # web_extract the top-2 pages per query for citable content
                extracted_content = ""
                if not _HERMES_RUNTIME and web_extract is None:
                    extracted_content = snippet  # fallback
                else:
                    try:
                        # Extract the current URL + one more from results for depth
                        urls_to_extract = [url]
                        for r2 in results[1:3]:
                            u2 = r2.get("url", "")
                            if u2 and u2 != url:
                                urls_to_extract.append(u2)
                                break
                        extract_result = web_extract(urls=urls_to_extract[:2], char_limit=3000)
                        for res in extract_result.get("results", []):
                            if res.get("url") == url and not res.get("error"):
                                extracted_content = res.get("content", "") or ""
                                break
                    except Exception as e:
                        extracted_content = snippet  # fallback to snippet on error

                # Use extracted content for librebase_delta + confidence
                delta_text = ""
                if feature in positioning:
                    strength = positioning[feature]["strength"]
                    if impact == "strong":
                        if strength == "weak":
                            delta_text = f"LibreBase is WEAK on {feature}; competitor is gaining ground here"
                        elif strength == "neutral":
                            delta_text = f"LibreBase NEUTRAL on {feature}; competitor is now strong — monitor"
                        else:
                            delta_text = f"LibreBase strong on {feature} but competitor is adding it — competitive pressure"
                    elif impact == "weak":
                        if strength == "strong":
                            delta_text = f"LibreBase STRONG on {feature}; competitor still weak — market this gap"
                        else:
                            delta_text = f"Competitor weak on {feature}; LibreBase position stable"
                    else:
                        delta_text = f"Tracking {feature} evolution for {name}"

                # Confidence boost from extracted content
                content_for_confidence = (extracted_content or snippet).lower()
                conf_boost = 0.0
                if impact == "strong" and any(k in content_for_confidence for k in ["mcp", "agent", "launch", "announce", "introducing", "new"]):
                    conf_boost = 0.1
                elif impact == "weak" and any(k in content_for_confidence for k in ["self-host", "open source", "simple", "lightweight"]):
                    conf_boost = 0.1

                finding = {
                    "competitor": name,
                    "competitor_url": comp_url or "",
                    "query": query,
                    "headline": title[:200],
                    "url": url,
                    "announced_feature": feature,
                    "impact": impact,
                    "librebase_delta": delta_text,
                    "raw_snippet": snippet[:500],
                    "content_excerpt": extracted_content[:1500] if extracted_content else snippet[:500],
                    "confidence": min(0.75 + conf_boost, 0.95),
                }
                findings.append(finding)
                total_queries += 1

        print(f"    → {len([f for f in findings if f['competitor'] == name])} findings")

    # ── Trend scans (general, once per day) ──────────────────────────────────
    print(f"\n  [trends] General BaaS/AI/cloud trend scan")
    for query in trend_queries():
        if dry_run:
            print(f"    [DRY] trend query: {query}")
            total_queries += 1
            continue

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

            c2 = sq2.connect(DB)
            c2.row_factory = sq2.Row
            existing = c2.execute(
                "SELECT id FROM daily_scans WHERE url=? AND date(scanned_at)=date('now')",
                (url,),
            ).fetchone()
            c2.close()
            if existing:
                continue

            feature, impact = classify_headline(title, url)
            if impact == "noise":
                continue  # skip trend noise

            # Content extraction for trends too
            extracted_content = ""
            if not _HERMES_RUNTIME and web_extract is None:
                extracted_content = snippet
            else:
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
                            extracted_content = res.get("content", "") or ""
                            break
                except Exception:
                    extracted_content = snippet

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
                "content_excerpt": extracted_content[:1000] if extracted_content else snippet[:500],
                "confidence": 0.65,
            }
            findings.append(finding)
            total_queries += 1

    print(f"\n  Total findings: {len(findings)}")
    print(f"  Total queries fired: {total_queries}")

    if dry_run:
        print("\n[DRY RUN] No data persisted. Rerun without --dry-run to execute.")
        return {"findings": len(findings), "queries": total_queries, "dry_run": True}

    # ── Strong-signal alerts ─────────────────────────────────────────────────
    strong_findings = [f for f in findings if f["impact"] == "strong"]
    if strong_findings:
        print(f"\n  ⚡ STRONG SIGNAL ALERTS ({len(strong_findings)} findings)")
        print(f"  ─────────────────────────────────────────────")
        alert_lines = []
        for sf in strong_findings[:20]:  # top 20
            # Extract the specific weak feature from librebase_delta
            delta = sf.get("librebase_delta", "")
            # Determine which feature from the finding itself
            fname = sf.get("announced_feature", "unknown")
            competitor = sf.get("competitor", "unknown")
            headline = sf.get("headline", "")
            url = sf.get("url", "")
            conf = sf.get("confidence", 0.75)

            alert_lines.append(f"  [{competitor}] {headline}")
            alert_lines.append(f"    Feature: {fname} | Confidence: {conf:.0%}")
            if url:
                alert_lines.append(f"    URL: {url}")
            if delta:
                alert_lines.append(f"    Delta: {delta}")
            alert_lines.append("")

        alert_text = "\n".join(alert_lines)
        print(alert_text)

        # Write alerts to a separate file for quick scanning
        alerts_path = os.path.join(
            LIBREBASE_DIR, "data", "marketing",
            f"strong_alerts_{date.today().isoformat()}.md"
        )
        with open(alerts_path, "w") as fh:
            fh.write(f"# LibreBase Strong Signal Alerts — {date.today().isoformat()}\n\n")
            fh.write(f"**{len(strong_findings)} strong signals detected.**\n\n")
            fh.write(alert_text)
        print(f"  → alerts written: {alerts_path}")

    # ── Persist via scan CLI ──────────────────────────────────────────────────
    print("\n  Persisting findings...")
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

    # ── Write digest file ─────────────────────────────────────────────────────
    digest_proc = subprocess.run(
        [sys.executable, SCAN_CLI, "--digest"],
        capture_output=True,
        text=True,
        cwd=LIBREBASE_DIR,
    )
    if digest_proc.returncode == 0:
        digest_md = digest_proc.stdout
        os.makedirs(os.path.dirname(DIGEST_FILE), exist_ok=True)
        with open(DIGEST_FILE, "w") as fh:
            fh.write(digest_md)
        print(f"  ✓ digest written: {DIGEST_FILE}")

    # ── Print digest to stdout ────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print(digest_proc.stdout)

    return {
        "findings": len(findings),
        "queries": total_queries,
        "digest_file": DIGEST_FILE,
    }


# ── CLI ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Unified LibreBase Daily Competitor Research"
    )
    parser.add_argument(
        "--scope",
        choices=["all", "baas", "cloud", "ai-platform", "paas", "backend", "cms-overlap", "trends-only"],
        default="all",
        help="Category scope filter (default: all). Use 'trends-only' for weekly trend deep-dive.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show queries only, don't run searches or persist",
    )
    args = parser.parse_args()

    result = run_daily_scan(scope=args.scope, dry_run=args.dry_run)
    print(f"\nDone: {json.dumps(result, indent=2)}")


def run_trend_only_scan() -> Dict[str, Any]:
    """Weekly deep-dive: scan ONLY general BaaS/AI/cloud trend queries.

    Called by the weekly cron or manually. No competitor-specific scanning.
    Writes to the same DB + digest file.
    """
    return run_daily_scan(scope="trends-only")
