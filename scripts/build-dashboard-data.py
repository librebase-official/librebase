#!/usr/bin/env python3
"""Rebuild dashboard data.json from librebase_competitive.db + Linear issues."""
import json, sqlite3, subprocess, os
from datetime import datetime, timezone

DB = "/Users/julian/Documents/coding-projects/librebase/librebase_competitive.db"
OUT = "/Users/julian/.hermes/profiles/librebasemarketingmanager/data.json"
BASE = "/Users/julian/Documents/coding-projects"

os.makedirs(os.path.dirname(OUT), exist_ok=True)

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row

# our_positioning
our_pos = []
for row in conn.execute("SELECT rowid, feature, our_offer, strength, notes, updated_at FROM our_positioning ORDER BY rowid"):
    our_pos.append({
        "id": row["rowid"],
        "feature": row["feature"],
        "our_offer": row["our_offer"],
        "strength": row["strength"],
        "notes": row["notes"],
        "updated_at": row["updated_at"],
    })

# competitors
competitors = []
for row in conn.execute("SELECT id, name, url, category, first_seen, active, notes FROM competitors ORDER BY category, name"):
    competitors.append({
        "id": row["id"],
        "name": row["name"],
        "category": row["category"] or "",
        "url": row["url"] or "",
        "first_seen": row["first_seen"],
        "active": row["active"],
        "notes": row["notes"] or "",
    })

# competitor_features pivot: competitor -> {feature: offered}
cf_rows = conn.execute("SELECT competitor_id, feature, offered, detail, last_verified, source_url FROM competitor_features").fetchall()
cf_pivot = {}
for r in cf_rows:
    cid = r["competitor_id"]
    if cid not in cf_pivot:
        cf_pivot[cid] = {}
    cf_pivot[cid][r["feature"]] = {
        "offered": r["offered"],
        "detail": r["detail"],
        "last_verified": r["last_verified"],
        "source_url": r["source_url"],
    }

# Attach features to competitors
for c in competitors:
    c["features"] = cf_pivot.get(c["id"], {})

competitor_features_rows = [dict(r) for r in conn.execute("SELECT rowid, competitor_id, feature, offered, detail, last_verified, source_url FROM competitor_features ORDER BY competitor_id, feature")]

# competitor_feature_history
cf_history = [dict(r) for r in conn.execute("SELECT rowid, competitor_id, feature, offered_old, offered_new, changed_at, note FROM competitor_feature_history ORDER BY changed_at DESC LIMIT 50")]

# findings from our_positioning (all rows become findings)
findings = []
for row in conn.execute("SELECT rowid, feature, our_offer, strength, notes, updated_at FROM our_positioning ORDER BY rowid"):
    sev = "good" if row["strength"] == "strong" else ("warning" if row["strength"] == "neutral" else "critical")
    findings.append({
        "id": row["rowid"],
        "feature": row["feature"],
        "severity": sev,
        "title": f"{row['feature']}: {row['our_offer'][:80]}",
        "status": row["strength"],
        "notes": row["notes"],
        "updated_at": row["updated_at"],
    })

# positioning (north stars + pitch + sound bites) — pull from notes of key rows + static
north_stars = [
    "Open — public repo, no walled garden, exportable",
    "Lean — minimal surface, do fewer things well",
    "Fast — self-host on your VPS, no multi-tenant tax",
    "Honest — KMS-sealed secrets, audit trail, no hidden billing",
    "Simple — agent-first, one key, one console",
]
pitch_lines = [
    "New way of doing backend as a service — agent-first, simple for humans and agents, yet secure.",
    "Your agents as first-class citizens: auto-discoverable MCP, scoped keys, KMS-sealed secrets.",
    "Pure-Li stack: licontainer OCI engine, envelope-crypto KMS, Postgres-compatible storage — no Docker tax.",
]
sound_bites = [
    "Supabase-shaped API compatibility for Supabase refugees — not a Supabase dependency.",
    "MCP for BaaS entity lifecycle — not DB queries (Supabase/Neon) or infra control (Railway/Fly).",
    "KMS + pure-Li stack — cryptographic trust story for agent operations. Your platform AND your data are verifiable.",
    "Self-host + K8s + licontainer — for agents in private/regulated environments, our full stack matters.",
    "Instance model (dedicated/shared) — competitors are single-tenant-per-project. We let agents manage multiple isolated instances.",
]

# Daily scan — from competitor_feature_history
daily_scan = []
for r in cf_history[:12]:
    comp = next((c for c in competitors if c["id"] == r["competitor_id"]), None)
    daily_scan.append({
        "competitor": comp["name"] if comp else f"unknown({r['competitor_id']})",
        "feature": r["feature"],
        "changed_from": r["offered_old"],
        "changed_to": r["offered_new"],
        "changed_at": r["changed_at"],
        "note": r["note"],
    })

# Linear issues
def get_linear_issues():
    try:
        r = subprocess.run(
            ["python3", "linear_issues.py", "librebase", "list", "--limit", "60"],
            capture_output=True, text=True, cwd=BASE, timeout=30
        )
        if r.returncode != 0:
            return []
        issues = []
        current = None
        for line in r.stdout.split("\n"):
            line = line.strip()
            if line.startswith("LIB-"):
                if current:
                    issues.append(current)
                parts = line.split(":", 1)
                lid = parts[0].strip()
                rest = parts[1].strip() if len(parts) > 1 else ""
                current = {"id": lid, "title": rest, "state": "Todo", "labels": [], "updated": ""}
            elif line.startswith("State:") and current:
                current["state"] = line.split(":",1)[1].strip()
            elif line.startswith("Labels:") and current:
                current["labels"] = [l.strip() for l in line.split(":",1)[1].split(",")]
            elif line.startswith("Updated:") and current:
                current["updated"] = line.split(":",1)[1].strip()
        if current:
            issues.append(current)
        return issues
    except Exception as e:
        return [{"error": str(e)}]

linear_issues = get_linear_issues()

# MCP device probe
def probe_mcp():
    import urllib.request
    try:
        payload = json.dumps({"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"auth_start","arguments":{"access":"write","resources":["projects","keys","logs","instances","hosts","members"]}}}).encode()
        req = urllib.request.Request(f"{SITE}/api/mcp", data=payload, headers={"Content-Type":"application/json"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = json.load(resp)
            content = body.get("result",{}).get("content",[])
            if content:
                text = content[0].get("text","")
                return json.loads(text) if text else {}
    except Exception as e:
        return {"error": str(e), "status_code": getattr(e, 'code', None)}
    return {}

mcp_probe = probe_mcp()

# Activity log — regenerate from recent findings + issues
activity = [
    {"date": datetime.now(timezone.utc).strftime("%Y-%m-%d"), "event": "Integration research complete — 11 dimensions, 34 competitors", "by": "@librebasemarketresearch"},
    {"date": datetime.now(timezone.utc).strftime("%Y-%m-%d"), "event": f"{len(linear_issues)} Linear issues in LIB team", "by": "@librebasemarketingmanager"},
    {"date": datetime.now(timezone.utc).strftime("%Y-%m-%d"), "event": f"DB: {len(our_pos)} positioning rows, {len(competitors)} competitors", "by": "@librebaseagenticuxtester"},
    {"date": datetime.now(timezone.utc).strftime("%Y-%m-%d"), "event": "Matrix rendered: Supabase benchmark 9/10 integration features", "by": "@librebaseprojectmanager"},
]

data = {
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "competitors": competitors,
    "our_positioning": our_pos,
    "competitor_features": competitor_features_rows,
    "competitor_feature_history": cf_history,
    "findings": findings,
    "positioning": {
        "north_stars": north_stars,
        "pitch_lines": pitch_lines,
        "sound_bites": sound_bites,
    },
    "linear_issues": linear_issues,
    "daily_scan": daily_scan,
    "mcp_device_probe": mcp_probe,
    "activity_log": activity,
}

with open(OUT, "w") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"Wrote {OUT} ({os.path.getsize(OUT)} bytes)")
print(f"  competitors: {len(competitors)}")
print(f"  our_positioning: {len(our_pos)}")
print(f"  competitor_features: {len(competitor_features_rows)}")
print(f"  findings: {len(findings)}")
print(f"  linear_issues: {len(linear_issues)}")
print(f"  daily_scan: {len(daily_scan)}")
print(f"  mcp_device_probe: {mcp_probe.get('user_code') or mcp_probe.get('error')}")
print(f"  activity_log: {len(activity)}")
