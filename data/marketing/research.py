#!/usr/bin/env python3
"""
Daily Competitor Research Script for Librebase Marketing Manager.

For each of the 28 tracked competitors and general BaaS/AI/cloud trends,
search the web, extract content, and store structured findings in the DB.

Run manually:  python3 research.py [--scope all|baas|cloud|ai-platform|backend]
Cron (04:30 CEST): configured separately via cronjob.

Output: DB records in findings + research_runs, optionally a markdown summary file.
"""

import argparse
import json
import os
import re
import sys
import textwrap
from datetime import datetime, timezone

# ── DB helpers ────────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))
from seed_db import get_conn

DB_PATH = os.path.join(os.path.dirname(__file__), "competitor_research.db")

# ── Web tools (Hermes) ────────────────────────────────────────────────────────
from hermes_tools import web_search, web_extract

MAX_FINDINGS_PER_COMPETITOR = 5  # avoid flooding; keep to most relevant 5/day
MAX_FINDINGS_TRENDS = 8          # general trend articles per run
SEARCH_QUERIES_PER_COMPETITOR = 2  # 2 searches per competitor: news + social

# ── Query templates ───────────────────────────────────────────────────────────
def queries_for_competitor(name: str, domain: str | None, category: str):
    """Generate 1-2 search queries for a competitor."""
    q1 = f"{name} announcement OR launch OR update OR new feature 2026"
    q2 = f"{name} blog OR news OR release"
    return [q1, q2]


def trend_queries():
    """General AI/cloud/BaaS trend queries."""
    return [
        "AI agent backend platform announcements 2026",
        "backend-as-a-service trends 2026",
        "serverless backend cloud new features 2026",
        "open source BaaS Supabase alternatives 2026",
        "AI cloud infrastructure developer tools 2026",
        "Postgres serverless edge compute announcements 2026",
        "real-time API backend platform comparison 2026",
        "developer tools AI agent SDK release 2026",
    ]


# ── Extraction logic ──────────────────────────────────────────────────────────
def extract_relevance(title: str, url: str, content: str, competitor_name: str) -> int:
    """Score 1-10 how relevant a finding is to Librebase (heuristic)."""
    score = 5
    name_lower = competitor_name.lower()
    text = (title + " " + content).lower()

    # Direct competitor mention + key BaaS topics
    keywords = ["supabase", "backend", "database", "postgres", "real-time",
                "realtime", "auth", "storage", "api", "saas", "open source",
                "self-host", "edge", "serverless", "cloud", "firebase",
                "agent", "llm", "ai", "sdk", "cli", "launch", "pricing",
                "free tier", "enterprise", "api change", "deprecation"]
    hits = sum(1 for k in keywords if k in text)
    score += min(hits, 4)

    # Score boost for actual product/announcement language
    product_flags = ["launch", "announce", "release", "new", "introduce",
                     "version", "update", "upgrade", "beta", "generally available",
                     "ga", "feature", "pricing", "plan", "integration",
                     "partnership", "acquire", "funding", "series"]
    if any(f in text for f in product_flags):
        score += 1

    return min(score, 10)


def estimate_sentiment(content: str, competitor_name: str) -> str:
    """Rough sentiment relative to Librebase's positioning."""
    text = content.lower()
    pos_signals = [
        "open source", "self-host", "free tier", "community", "plugin",
        "extension", "sdk", "developer experience", "easy", "simple",
        "lightweight", "fast", "cheap", "affordable", "transparent",
        "developer-first", "beta", "early access"
    ]
    neg_signals = [
        "outage", "incident", "bug", "down", "deprecated", "shut down",
        "pricing increase", "price hike", "expensive", "enterprise only",
        "paywall", "locked", "limited", "sunset", "discontinued"
    ]
    enterprise_pos = [
        "enterprise", "security", "compliance", "sso", "rbac", "audit",
        "sla", "support", "scal"
    ]
    ai_pos = ["agent", "llm", "ai", "model", "embedding", "rag", "function calling"]

    pos = sum(1 for s in pos_signals if s in text)
    neg = sum(1 for s in neg_signals if s in text)
    ent = sum(1 for s in enterprise_pos if s in text)
    ai = sum(1 for s in ai_pos if s in text)

    if neg > pos:
        return "negative"
    if ai > 1 and ent > 1:
        return "neutral"  # enterprise AI push — competitive but not directly threatening
    if pos >= 3:
        return "positive"
    return "neutral"


# ── Main research loop ────────────────────────────────────────────────────────
def run(scope: str = "all", output_md: str | None = None):
    conn = get_conn()
    now = datetime.now(timezone.utc)
    run_date = now.strftime("%Y-%m-%d")
    started_at = now.isoformat()

    # Determine which competitors to scan
    if scope == "all":
        comps = conn.execute(
            "SELECT * FROM competitors WHERE status='active' ORDER BY category, name"
        ).fetchall()
    else:
        comps = conn.execute(
            "SELECT * FROM competitors WHERE status='active' AND category=? ORDER BY name",
            (scope,),
        ).fetchall()

    run_id = conn.execute(
        """INSERT INTO research_runs (run_date, source, scope, started_at, status)
           VALUES (?, 'daily-cron', ?, ?, 'in-progress')""",
        (run_date, scope, started_at),
    ).lastrowid

    print(f"[research] Run #{run_id} | scope={scope} | {len(comps)} competitors | started {started_at}")

    total_findings = 0
    findings_batch = []  # accumulate for DB insert

    # ── Competitor scans ──────────────────────────────────────────────────────
    for comp in comps:
        name = comp["name"]
        domain = comp["domain"]
        category = comp["category"]
        homepage = comp["homepage_url"]

        print(f"  [{category}] {name} ...")

        found = 0
        for qi, query in enumerate(queries_for_competitor(name, domain, category)):
            try:
                search_result = web_search(query, limit=5)
            except Exception as e:
                print(f"    search #{qi+1} failed: {e}")
                continue

            results = search_result.get("data", {}).get("web", [])
            if not results:
                continue

            for r in results:
                if found >= MAX_FINDINGS_PER_COMPETITOR:
                    break

                url = r.get("url", "")
                title = r.get("title", "")
                description = r.get("description", "")

                # Skip if we already have this URL in findings today (dedupe)
                existing = conn.execute(
                    "SELECT id FROM findings WHERE url=? AND run_id=?",
                    (url, run_id),
                ).fetchone()
                if existing:
                    continue

                # Extract content (light — we don't need full pages, just enough for sentiment + tags)
                try:
                    extract_result = web_extract(urls=[url], char_limit=4000)
                    content = ""
                    for res in extract_result.get("results", []):
                        if res.get("url") == url and not res.get("error"):
                            content = res.get("content", "") or ""
                            break
                except Exception:
                    content = description  # fallback to search snippet

                if not content.strip():
                    content = description

                # Determine the publishing date if possible from URL or content
                published_at = None
                m = re.search(r"/(\d{4})/(\d{2})/(\d{2})", url)
                if m:
                    published_at = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"

                # Find which competitor this belongs to (might be a general article mentioning multiple)
                assigned_competitor_id = comp["id"]
                if domain and domain in url:
                    assigned_competitor_id = comp["id"]

                relevance = extract_relevance(title, url, content, name)
                if relevance < 3:
                    continue  # skip low-relevance noise

                sentiment = estimate_sentiment(content, name)
                finding_type = _classify_type(title, url, content)

                f_row = (
                    run_id,
                    assigned_competitor_id,
                    title[:250],
                    url,
                    content[:4000],
                    finding_type,
                    sentiment,
                    relevance,
                    published_at,
                    now.isoformat(),
                )
                findings_batch.append(f_row)
                found += 1
                total_findings += 1

            if found >= MAX_FINDINGS_PER_COMPETITOR:
                break

        # Update competitor last check
        conn.execute(
            "UPDATE competitor_socials SET last_check=? WHERE competitor_id=?",
            (now.isoformat(), comp["id"]),
        )

    # ── General trend scans ───────────────────────────────────────────────────
    print(f"  [trends] scanning general BaaS/AI/cloud trend articles ...")
    for query in trend_queries():
        if total_findings >= MAX_FINDINGS_TRENDS + len(comps) * 2:
            break
        try:
            search_result = web_search(query, limit=3)
        except Exception as e:
            print(f"    trend search failed: {e}")
            continue

        results = search_result.get("data", {}).get("web", [])
        for r in results:
            if total_findings >= MAX_FINDINGS_TRENDS:
                break
            url = r.get("url", "")
            title = r.get("title", "")
            description = r.get("description", "")

            # Dedupe
            existing = conn.execute(
                "SELECT id FROM findings WHERE url=? AND run_id=?",
                (url, run_id),
            ).fetchone()
            if existing:
                continue

            try:
                extract_result = web_extract(urls=[url], char_limit=3000)
                content = ""
                for res in extract_result.get("results", []):
                    if res.get("url") == url and not res.get("error"):
                        content = res.get("content", "") or ""
                        break
            except Exception:
                content = description

            if not content.strip():
                content = description

            relevance = extract_relevance(title, url, content or "", "general")
            if relevance < 4:
                continue

            sentiment = estimate_sentiment(content or "", "general")
            finding_type = _classify_type(title, url, content or "")

            f_row = (
                run_id,
                None,  # no specific competitor
                title[:250],
                url,
                content[:3000],
                finding_type,
                sentiment,
                relevance,
                None,
                now.isoformat(),
            )
            findings_batch.append(f_row)
            total_findings += 1

    # ── Bulk insert findings ──────────────────────────────────────────────────
    if findings_batch:
        conn.executemany(
            """INSERT INTO findings
               (run_id, competitor_id, title, url, content, finding_type,
                sentiment, relevance, published_at, crawled_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            findings_batch,
        )
        conn.commit()
        print(f"  → inserted {len(findings_batch)} findings")

    # ── Auto-tag findings ─────────────────────────────────────────────────────
    _auto_tag_findings(conn, run_id)

    # ── Finalize run ──────────────────────────────────────────────────────────
    now_end = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """UPDATE research_runs
           SET status='done', finished_at=?, competitor_count=?, finding_count=?
           WHERE id=?""",
        (now_end, len(comps), len(findings_batch), run_id),
    )
    conn.commit()
    conn.close()

    summary = _build_summary(conn if False else None, run_id, scope, len(comps), len(findings_batch))
    # Re-open to build summary (DB is closed above)
    conn2 = get_conn()
    summary = _build_summary_from_db(conn2, run_id, scope, len(comps), len(findings_batch))
    conn2.close()

    if output_md:
        with open(output_md, "w") as fh:
            fh.write(summary)
        print(f"  → summary written to {output_md}")

    print(f"[research] Done. run_id={run_id}, {len(findings_batch)} findings stored.")
    return summary


def _classify_type(title: str, url: str, content: str) -> str:
    """Heuristic: classify finding_type from title/content."""
    t = (title + " " + content).lower()
    if any(w in t for w in ["funding", "series a", "series b", "series c", "raise", "vc", "investor", "acquisition", "acquired"]):
        return "pricing-changes" if "pricing" in t else "funding"  # map funding mentions
    if "pricing" in t or "price" in t or "plan" in t or "tier" in t:
        return "pricing-changes"
    if any(w in t for w in ["launch", "new feature", "release", "generally available", "beta", "preview", "introduce"]):
        return "feature-launch"
    if any(w in t for w in ["sdk", "cli", "client library", "python", "typescript", "go", "rust", "api", "endpoint"]):
        return "sdk-release"
    if any(w in t for w in ["blog", "tutorial", "guide", "how to", "walkthrough"]):
        return "blog-post"
    if any(w in t for w in ["twitter", "x", "reddit", "discussion", "thread"]):
        return "social"
    if "hiring" in t or "job" in t or "careers" in t or "we're hiring" in t:
        return "hiring"
    return "announcement"


def _auto_tag_findings(conn, run_id: int):
    """Assign trend_tags to newly inserted findings based on content keywords."""
    findings = conn.execute(
        "SELECT id, content FROM findings WHERE run_id=? AND crawled_at > datetime('now', '-2 hours')",
        (run_id,),
    ).fetchall()

    for f in findings:
        content = (f["content"] or "").lower()
        title = ""
        if f"[finding_id={f['id']}]" in content:
            pass  # not needed

        tags_to_add = []
        # Keyword → tag mapping
        mapping = [
            (["ai agent", "agentic", "agent framework", "agent sdk", "autonomous agent"], "ai-agents"),
            (["function calling", "tool use", "tool calling", "mcp", "model context protocol"], "agentic-ux"),
            (["llm", "large language model", "gpt", "claude", "gemini", "chatbot"], "llm-saas"),
            (["gpu", "inference", "model serving", "model deployment", "baseten", "replicate"], "ai-cloud-infra"),
            (["serverless", "edge function", "cold start", "lambda", "cloud function"], "serverless"),
            (["edge", "cloudflare", "fly.io", "distributed"], "edge-compute"),
            (["kubernetes", "k8s", "helm", "container", "pod"], "kubernetes"),
            (["postgres", "postgresql", "sql", "database", "sqlite"], "postgres"),
            (["realtime", "websocket", "subscription", "live", "sync"], "realtime"),
            (["auth", "login", "signin", "sign-in", "oauth", "sso", "identity", "jwt"], "auth"),
            (["open source", "self-host", "self hosted", "docker", "license"], "open-source-baas"),
            (["alternative", "vs", "comparison", "competitor", "versus"], "supabase-alternatives"),
            (["pricing", "price", "plan", "tier", "free tier", "pay as you go", "cost"], "pricing-changes"),
            (["funding", "series", "raise", "vc", "invest", "acquisition", "acquire"], "funding"),
            (["hiring", "job", "careers", "we're hiring", "engineering", "team"], "hiring"),
            (["github stars", "community", "adoption", "users", "downloads"], "developer-adoption"),
            (["sdk", "cli", "client library", "api"], "sdk-release"),
            (["documentation", "docs", "guide", "tutorial"], "documentation"),
            (["enterprise", "sso", "rbac", "audit", "sla", "compliance", "security"], "enterprise-features"),
            (["rebrand", "position", "messaging", "new direction"], "go-to-market"),
        ]
        for keywords, tag_name in mapping:
            if any(kw in content for kw in keywords):
                tag_id = conn.execute(
                    "SELECT id FROM trend_tags WHERE name=?", (tag_name,)
                ).fetchone()
                if tag_id:
                    tags_to_add.append(tag_id["id"])

        if tags_to_add:
            conn.executemany(
                "INSERT OR IGNORE INTO finding_tags (finding_id, tag_id) VALUES (?, ?)",
                [(f["id"], tid) for tid in set(tags_to_add)],
            )
    conn.commit()


def _build_summary_from_db(conn, run_id: int, scope: str, comp_count: int, finding_count: int):
    """Build a markdown summary of the research run from the DB."""
    lines = []
    lines.append(f"# Librebase Competitor Research — {conn.execute('SELECT run_date FROM research_runs WHERE id=?', (run_id,)).fetchone()['run_date']}")
    lines.append("")
    lines.append(f"**Scope:** {scope} | **Competitors scanned:** {comp_count} | **Findings:** {finding_count}")
    lines.append("")

    # Group findings by type
    findings = conn.execute(
        """SELECT f.*, c.name as competitor_name
           FROM findings f
           LEFT JOIN competitors c ON c.id = f.competitor_id
           WHERE f.run_id = ?
           ORDER BY f.relevance DESC, f.crawled_at DESC""",
        (run_id,),
    ).fetchall()

    if not findings:
        lines.append("*No findings this run. — Check back later.*")
        return "\n".join(lines)

    # Group by competitor (or "General trends")
    by_comp = {}
    for f in findings:
        key = f["competitor_name"] or "📰 General trends / market"
        by_comp.setdefault(key, []).append(f)

    for comp_name, items in sorted(by_comp.items(), key=lambda x: (x[0] == "📰 General trends / market", x[0])):
        lines.append(f"## {comp_name}")
        lines.append("")
        for f in items[:5]:  # top 5 per competitor in summary
            sentiment_icon = {"positive": "🟢", "neutral": "🟡", "negative": "🔴"}.get(f["sentiment"], "⬜")
            tag_ids = conn.execute(
                "SELECT t.name FROM trend_tags t JOIN finding_tags ft ON ft.tag_id=t.id WHERE ft.finding_id=?",
                (f["id"],),
            ).fetchall()
            tags = ", ".join(t["name"] for t in tag_ids) if tag_ids else "—"

            url_line = f"[{f['url']}]" if f["url"] else ""
            lines.append(f"- {sentiment_icon} **[{f['finding_type']}]** {f['title']} {url_line}")
            lines.append(f"  _Tags: {tags} · Relevance: {f['relevance']}/10 · {f['crawled_at'][:16]}_")
            # Truncated content preview
            preview = (f["content"] or "")[:200].replace("\n", " ")
            if preview:
                lines.append(f"  {preview}...")
            lines.append("")

    return "\n".join(lines)


# ── CLI ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Daily Librebase competitor research")
    parser.add_argument(
        "--scope",
        choices=["all", "baas", "cloud", "ai-platform", "backend", "trends-only"],
        default="all",
        help="Competitor category scope (default: all)",
    )
    parser.add_argument(
        "--output",
        help="Write markdown summary to this file path (optional)",
    )
    args = parser.parse_args()

    if args.scope == "trends-only":
        # Only scan general trends
        pass  # handled inside run() by comp filter

    summary = run(scope=args.scope, output_md=args.output)
    print(summary)
