#!/usr/bin/env python3
"""
LibreBase Competitive Intelligence — daily scan persist + digest CLI.
======================================================================
Called by the cron agent AFTER it has run web_search/web_extract.
Feed it a JSON array of scan findings on stdin; it persists them and
prints a digest to stdout.

Input schema (one object per finding):
{
  "competitor": "Supabase",            # known competitor name OR "new" for discovery
  "competitor_url": "https://...",    # optional
  "query": "supabase new features 2026",
  "headline": "Supabase launches AI embeddings",
  "url": "https://supabase.com/blog/...",
  "announced_feature": "vector-embeddings",
  "impact": "strong|weak|new-competitor|noise",
  "librebase_delta": "We are weak here; competitor now leads on vector search",
  "raw_snippet": "Supabase today announced...",
  "confidence": 0.85
}

If competitor == "new", the row goes to discovery_log with disposition
decided by the caller (passed as "disposition").

Usage:
  echo '[...]' | python3 librebase_competitive_scan.py
  python3 librebase_competitive_scan.py --digest          # print today's digest
  python3 librebase_competitive_scan.py --status          # compact DB status
  python3 librebase_competitive_scan.py --changes SinceYYYY-MM-DD  # feature changes
"""

from librebase_competitive_db import store_daily_digest
from typing import Optional, Dict, List, Any
import json
import sqlite3
import sys
import os
from datetime import date, datetime
from collections import defaultdict

DB_PATH = os.environ.get(
    "LIBREBASE_COMPETITIVE_DB",
    os.path.expanduser("~/Documents/coding-projects/librebase/librebase_competitive.db"),
)

FEATURE_NAMES: List[str] = [
    "postgresql-db", "auth", "storage", "realtime", "mcp-agent-api",
    "agent-docs", "self-host", "kubernetes", "container-runtime",
    "billing-plans", "open-source", "console-studio", "edge-functions",
    "graphql", "row-level-security", "vector-embeddings", "instance-model",
    "kms-crypto", "billing-metering", "discounts-codes", "waitlist",
    "multi-region", "custom-domains", "delete-endpoints",
]

IMPACT_LABELS = {
    "strong": "🔴 LibreBase WEAK — competitor strong (attack surface)",
    "weak":   "🟢 LibreBase STRONG — competitor weak (defend + market)",
    "neutral":"⚪ Comparable — keep watching",
    "new-competitor": "🆕 New competitor discovered",
    "noise":  "· noise / logged for record",
}

FEATURE_LABELS = {
    "postgresql-db": "PostgreSQL DB",
    "auth": "Auth",
    "storage": "Storage",
    "realtime": "Realtime",
    "mcp-agent-api": "MCP / Agent API",
    "agent-docs": "Agent Docs",
    "self-host": "Self-host",
    "kubernetes": "Kubernetes",
    "container-runtime": "Container Runtime",
    "billing-plans": "Billing Plans",
    "open-source": "Open Source",
    "console-studio": "Console / Studio",
    "edge-functions": "Edge Functions",
    "graphql": "GraphQL",
    "row-level-security": "RLS",
    "vector-embeddings": "Vector / Embeddings",
    "instance-model": "Instance Model",
    "kms-crypto": "KMS / Crypto",
    "billing-metering": "Billing Metering",
    "discounts-codes": "Discount Codes",
    "waitlist": "Waitlist",
    "multi-region": "Multi-region",
    "custom-domains": "Custom Domains",
    "delete-endpoints": "Delete Endpoints",
}


def get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def normalize_competitor_name(name: str) -> Optional[str]:
    """Return canonical competitor name if known, else None."""
    if not name:
        return None
    key = name.strip().lower()
    conn = get_conn()
    row = conn.execute(
        "SELECT name FROM competitors WHERE LOWER(name) = ?", (key,)
    ).fetchone()
    conn.close()
    return row["name"] if row else None


def persist_findings(findings: List[Dict[str, Any]]) -> Dict[str, int]:
    """Insert findings into daily_scans + discovery_log + feature_history.
    Returns stats dict."""
    conn = get_conn()
    cur = conn.cursor()
    now_dt = datetime.now().isoformat()
    now_date = date.today().isoformat()

    scanned = 0
    strong = 0
    weak = 0
    new_comp = 0
    noise = 0
    unknown_comp = 0
    feature_changes = 0

    # Build name→id map for feature-delta tracking
    name_to_id = dict(
        conn.execute("SELECT name, id FROM competitors").fetchall()
    )

    for f in findings:
        competitor_raw = (f.get("competitor") or "").strip()
        impact = (f.get("impact") or "noise").strip().lower()
        headline = f.get("headline", "") or ""
        url = f.get("url", "") or ""
        query = f.get("query", "") or ""
        announced_feature = (f.get("announced_feature") or "").strip()
        librebase_delta = (f.get("librebase_delta") or "").strip()
        raw_snippet = (f.get("raw_snippet") or "").strip()
        confidence = float(f.get("confidence", 0.5))
        competitor_url = (f.get("competitor_url") or "").strip()
        disposition = (f.get("disposition") or "").strip()

        # Resolve competitor
        canonical = normalize_competitor_name(competitor_raw) if competitor_raw else None
        if competitor_raw.lower() == "new":
            canonical = None  # discovery path

        if canonical:
            cid = name_to_id.get(canonical)
        else:
            cid = None
            if competitor_raw and competitor_raw.lower() != "new":
                unknown_comp += 1

        # ── daily_scans row ──
        cur.execute(
            """INSERT INTO daily_scans
               (scanned_at, competitor_id, query, headline, url, announced_feature,
                impact, librebase_delta, raw_snippet, parse_confidence)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (
                now_dt, cid, query, headline, url, announced_feature,
                impact, librebase_delta, raw_snippet, confidence,
            ),
        )
        scanned += 1
        if impact == "strong":
            strong += 1
        elif impact == "weak":
            weak += 1
        elif impact == "new-competitor":
            new_comp += 1
        elif impact == "noise":
            noise += 1

        # ── discovery_log (for "new" or unknown) ──
        if not canonical:
            disp = disposition or ("uncertain" if competitor_raw and competitor_raw.lower() != "new" else "not-a-competitor")
            cur.execute(
                """INSERT INTO discovery_log (scanned_at, query, candidate_name, candidate_url, disposition, notes)
                   VALUES (?,?,?,?,?,?)""",
                (now_dt, query, competitor_raw if competitor_raw else None,
                 competitor_url or None, disp,
                 f"headline: {headline}" if headline else None),
            )

        # ── feature_delta tracking ──
        # If the finding names a known LibreBase feature and a known competitor,
        # and the impact is 'strong' or 'weak', record a feature_history entry
        # (compare against what we already have in competitor_features).
        if canonical and cid and announced_feature and announced_feature in FEATURE_NAMES:
            existing = conn.execute(
                "SELECT offered, detail, last_verified FROM competitor_features WHERE competitor_id=? AND feature=?",
                (cid, announced_feature),
            ).fetchone()

            # Heuristic: 'strong' impact on us means competitor is strong on this feature.
            # Set offered=1 (they have it). 'weak' means they're weak → offered=0 or keep.
            reason = None
            if impact == "strong":
                new_offered = 1
                reason = f"Daily scan {now_date}: {impact} — {headline} [{url}]"
            elif impact == "weak":
                new_offered = 0
                reason = f"Daily scan {now_date}: {impact} — {headline} [{url}]"
            else:
                new_offered = None  # don't change

            if new_offered is not None and existing:
                old_state = existing["offered"]
                if old_state != new_offered:
                    cur.execute(
                        """INSERT INTO competitor_feature_history
                           (competitor_id, feature, old_state, new_state, changed_at, reason, source_url)
                           VALUES (?,?,?,?,?,?,?)""",
                        (cid, announced_feature, old_state, new_offered, now_dt, reason or "", url),
                    )
                    # Update competitor_features
                    cur.execute(
                        """UPDATE competitor_features
                           SET offered=?, detail=?, last_verified=?, source_url=?
                           WHERE competitor_id=? AND feature=?""",
                        (new_offered,
                         f"{existing['detail']} | updated {now_date}: {headline}" if existing["detail"] else headline,
                         now_date, url, cid, announced_feature),
                    )
                    feature_changes += 1

    conn.commit()
    conn.close()
    return {
        "scanned": scanned,
        "strong": strong,
        "weak": weak,
        "new_competitor": new_comp,
        "noise": noise,
        "unknown_competitor": unknown_comp,
        "feature_changes": feature_changes,
    }


def build_digest() -> str:
    """Build today's digest as a markdown string."""
    conn = get_conn()
    today = date.today().isoformat()

    # Today's scans
    rows = conn.execute(
        """SELECT ds.id, c.name as competitor, ds.query, ds.headline, ds.url,
                  ds.announced_feature, ds.impact, ds.librebase_delta, ds.raw_snippet,
                  ds.parse_confidence, ds.scanned_at
           FROM daily_scans ds
           LEFT JOIN competitors c ON c.id = ds.competitor_id
           WHERE date(ds.scanned_at) = ?
           ORDER BY ds.scanned_at""",
        (today,),
    ).fetchall()

    # Feature changes today
    changes = conn.execute(
        """SELECT cfh.competitor_id, c.name, cfh.feature, cfh.old_state, cfh.new_state,
                  cfh.reason, cfh.source_url, cfh.changed_at
           FROM competitor_feature_history cfh
           JOIN competitors c ON c.id = cfh.competitor_id
           WHERE date(cfh.changed_at) = ?
           ORDER BY cfh.changed_at""",
        (today,),
    ).fetchall()

    # New competitors tracked today
    new_tracked = conn.execute(
        """SELECT dl.candidate_name, dl.candidate_url, dl.disposition, dl.notes, dl.scanned_at
           FROM discovery_log dl
           WHERE date(dl.scanned_at) = ? AND dl.disposition = 'new-tracked'
           ORDER BY dl.scanned_at""",
        (today,),
    ).fetchall()

    lines = []
    lines.append(f"# LibreBase Competitive Intelligence — Daily Scan {today}")
    lines.append("")
    lines.append(f"Scanned {len(rows)} findings today across {len(set(r['competitor'] for r in rows if r['competitor']))} known competitors.")
    lines.append("")

    # ── ⚡ Strong-signal alert summary (top of digest) ──────────────────────
    strong_items = [r for r in rows if r["impact"] == "strong"]
    if strong_items:
        lines.append("## 🚨 STRONG SIGNAL ALERTS")
        lines.append("")
        lines.append("_These findings indicate a competitor is strong on a feature where LibreBase is weak or neutral. Action recommended._")
        lines.append("")

        for r in strong_items:
            comp = r["competitor"] or "(new/unresolved)"
            has_content = bool(r["raw_snippet"] and r["raw_snippet"].strip())
            conf_pct = int(r["parse_confidence"] * 100)

            lines.append(f"### {comp} — {r['headline']}")
            lines.append("")
            lines.append(f"- **Feature:** `{r['announced_feature'] or 'N/A'}`")
            lines.append(f"- **Impact:** \U0001f534 strong (competitor gaining on LibreBase)")
            lines.append(f"- **Confidence:** {conf_pct}%")
            lines.append(f"- **Source:** [{r['url']}]({r['url']})" if r["url"] else "- **Source:** N/A")
            if r["librebase_delta"]:
                lines.append(f"- **LibreBase delta:** {r['librebase_delta']}")
            if has_content:
                excerpt = r["raw_snippet"][:300].replace("\n", " ")
                lines.append(f"- **Snippet:** {excerpt}...")
            lines.append("")

    # ── Feature changes ──
    if changes:
        lines.append("## 📈 Feature Changes (today)")
        lines.append("")
        for c in changes:
            old_label = {0: "none", 1: "yes", 2: "partial"}.get(c["old_state"], str(c["old_state"]))
            new_label = {0: "none", 1: "yes", 2: "partial"}.get(c["new_state"], str(c["new_state"]))
            arrow = "⬆️" if c["new_state"] > c["old_state"] else "⬇️" if c["new_state"] < c["old_state"] else "➡️"
            lines.append(f"- **{c['name']}** — `{c['feature']}` {old_label} → {new_label} {arrow}")
            lines.append(f"  - {c['reason']}")
            if c["source_url"]:
                lines.append(f"  - Source: {c['source_url']}")
        lines.append("")

    # ── New competitors tracked ──
    if new_tracked:
        lines.append("## 🆕 New Competitors Tracked (today)")
        lines.append("")
        for n in new_tracked:
            lines.append(f"- **{n['candidate_name']}** — {n['candidate_url'] or 'no URL'}")
            if n['notes']:
                lines.append(f"  - {n['notes']}")
        lines.append("")

    # ── Signals by impact ──
    strong_items = [r for r in rows if r["impact"] == "strong"]
    weak_items = [r for r in rows if r["impact"] == "weak"]
    other_items = [r for r in rows if r["impact"] not in ("strong", "weak")]

    if strong_items:
        lines.append("## 🔴 Where LibreBase Is WEAK (attack surface — competitor strong)")
        lines.append("")
        for r in strong_items:
            comp = r["competitor"] or "(new/unresolved)"
            lines.append(f"### {comp} — {r['headline']}")
            lines.append("")
            lines.append(f"- **Announced:** {r['announced_feature'] or 'N/A'}")
            lines.append(f"- **Source:** [{r['url']}]({r['url']})" if r["url"] else "- **Source:** N/A")
            if r["librebase_delta"]:
                lines.append(f"- **LibreBase delta:** {r['librebase_delta']}")
            if r["raw_snippet"]:
                snippet = r["raw_snippet"][:400]
                lines.append(f"- **Snippet:** {snippet}")
            lines.append(f"- **Confidence:** {r['parse_confidence']:.0%}")
            lines.append("")

    if weak_items:
        lines.append("## 🟢 Where LibreBase Is STRONG (competitor weak — defend + market)")
        lines.append("")
        for r in weak_items:
            comp = r["competitor"] or "(new/unresolved)"
            lines.append(f"### {comp} — {r['headline']}")
            lines.append("")
            lines.append(f"- **Announced:** {r['announced_feature'] or 'N/A'}")
            lines.append(f"- **Source:** [{r['url']}]({r['url']})" if r["url"] else "- **Source:** N/A")
            if r["librebase_delta"]:
                lines.append(f"- **LibreBase delta:** {r['librebase_delta']}")
            lines.append(f"- **Confidence:** {r['parse_confidence']:.0%}")
            lines.append("")

    if other_items:
        lines.append("## ⚪ Other (noise / new-competitor / neutral — logged for record)")
        lines.append("")
        for r in other_items:
            comp = r["competitor"] or "(new/unresolved)"
            impact_label = IMPACT_LABELS.get(r["impact"], r["impact"])
            lines.append(f"- **{comp}** — {r['headline']}  *( {impact_label} )*")
            if r["url"]:
                lines.append(f"  - {r['url']}")
        lines.append("")

    if not rows:
        lines.append("_No scans recorded today yet._")
        lines.append("")

    # ── Today's query coverage ──
    queries = sorted(set(r["query"] for r in rows if r["query"]))
    if queries:
        lines.append("## 🔎 Queries run today")
        lines.append("")
        for q in queries:
            lines.append(f"- {q}")
        lines.append("")

    conn.close()
    return "\n".join(lines)


def print_digest():
    print(build_digest())


def print_status():
    """Compact DB status: competitors, today's scan count, feature-change count."""
    conn = get_conn()
    today = date.today().isoformat()

    total_comp = conn.execute("SELECT COUNT(*) FROM competitors").fetchone()[0]
    active_comp = conn.execute("SELECT COUNT(*) FROM competitors WHERE active=1").fetchone()[0]
    today_scans = conn.execute(
        "SELECT COUNT(*) FROM daily_scans WHERE date(scanned_at) = ?", (today,)
    ).fetchone()[0]
    today_strong = conn.execute(
        "SELECT COUNT(*) FROM daily_scans WHERE date(scanned_at) = ? AND impact='strong'", (today,)
    ).fetchone()[0]
    today_weak = conn.execute(
        "SELECT COUNT(*) FROM daily_scans WHERE date(scanned_at) = ? AND impact='weak'", (today,)
    ).fetchone()[0]
    total_scans = conn.execute("SELECT COUNT(*) FROM daily_scans").fetchone()[0]
    total_changes = conn.execute("SELECT COUNT(*) FROM competitor_feature_history").fetchone()[0]
    tracked_comps = conn.execute(
        "SELECT COUNT(*) FROM competitors WHERE active=1"
    ).fetchone()[0]

    print(f"DB: {DB_PATH}")
    print(f"Competitors tracked: {total_comp} (active: {active_comp})")
    print(f"Today's scans: {today_scans}  (strong: {today_strong}, weak: {today_weak})")
    print(f"Total scans logged: {total_scans}")
    print(f"Total feature-history changes: {total_changes}")
    print(f"Positioning features tracked: {len(FEATURE_NAMES)}")
    conn.close()


def print_changes(since: str):
    """Show feature changes since a date (YYYY-MM-DD)."""
    conn = get_conn()
    rows = conn.execute(
        """SELECT c.name, cfh.feature, cfh.old_state, cfh.new_state,
                  cfh.reason, cfh.source_url, cfh.changed_at
           FROM competitor_feature_history cfh
           JOIN competitors c ON c.id = cfh.competitor_id
           WHERE date(cfh.changed_at) >= ?
           ORDER BY cfh.changed_at""",
        (since,),
    ).fetchall()

    if not rows:
        print(f"No feature changes since {since}.")
        return

    print(f"Feature changes since {since} ({len(rows)} rows):")
    print()
    for r in rows:
        old_l = {0: "none", 1: "yes", 2: "partial"}.get(r["old_state"], str(r["old_state"]))
        new_l = {0: "none", 1: "yes", 2: "partial"}.get(r["new_state"], str(r["new_state"]))
        arrow = "↑" if r["new_state"] > r["old_state"] else "↓" if r["new_state"] < r["old_state"] else "="
        print(f"  {r['changed_at']}  {r['name']:15s}  {r['feature']:22s}  {old_l} → {new_l} {arrow}")
        print(f"    {r['reason']}")
        if r["source_url"]:
            print(f"    Source: {r['source_url']}")
        print()


# ── CLI ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "--digest":
            markdown = build_digest()
            print(markdown)
        elif cmd == "--store-digest":
            markdown = build_digest()
            today = date.today().isoformat()
            # Build summary JSON
            conn = get_conn()
            scans = conn.execute(
                "SELECT COUNT(*) FROM daily_scans WHERE date(scanned_at) = ?", (today,)
            ).fetchone()[0]
            strong = conn.execute(
                "SELECT COUNT(*) FROM daily_scans WHERE date(scanned_at) = ? AND impact='strong'", (today,)
            ).fetchone()[0]
            weak = conn.execute(
                "SELECT COUNT(*) FROM daily_scans WHERE date(scanned_at) = ? AND impact='weak'", (today,)
            ).fetchone()[0]
            changes = conn.execute(
                "SELECT COUNT(*) FROM competitor_feature_history WHERE date(changed_at) = ?", (today,)
            ).fetchone()[0]
            conn.close()
            import json as _json
            summary = _json.dumps({
                "scanned_today": scans,
                "strong_count": strong,
                "weak_count": weak,
                "feature_changes": changes,
                "digest_date": today,
                "stored_at": datetime.now().isoformat(),
            }, indent=2)
            source_file = os.path.join(os.path.dirname(DB_PATH), f"competitive_digest_{today}.md")
            store_daily_digest(get_conn(), today, markdown, summary, source_file)
            # Also write the file
            with open(source_file, "w") as f:
                f.write(markdown + "\n")
            print(f"Stored digest for {today} → daily_digests + {source_file}")
            print(f"  scans={scans}, strong={strong}, weak={weak}, changes={changes}")
        elif cmd == "--status":
            print_status()
        elif cmd == "--changes" and len(sys.argv) > 2:
            print_changes(sys.argv[2])
        else:
            print(f"Usage: {sys.argv[0]} < findings.json", file=sys.stderr)
            print(f"       {sys.argv[0]} --digest", file=sys.stderr)
            print(f"       {sys.argv[0]} --status", file=sys.stderr)
            print(f"       {sys.argv[0]} --changes YYYY-MM-DD", file=sys.stderr)
            sys.exit(1)
    else:
        # Read JSON from stdin
        raw = sys.stdin.read()
        if not raw.strip():
            print("No input on stdin. Pipe a JSON array of findings or use --digest/--status.", file=sys.stderr)
            sys.exit(1)
        findings = json.loads(raw)
        if not isinstance(findings, list):
            findings = [findings]
        stats = persist_findings(findings)
        print(json.dumps(stats, indent=2))
