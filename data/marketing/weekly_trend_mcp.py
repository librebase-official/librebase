#!/usr/bin/env python3
"""Standalone LibreBase weekly trend scanner — uses direct HTTP to Hermes MCP."""
import json, os, sys, urllib.request, sqlite3, subprocess
from datetime import date

LIBREBASE_DIR = os.path.expanduser("~/Documents/coding-projects/librebase")
DB_PATH = os.path.join(LIBREBASE_DIR, "librebase_competitive.db")
MARKETING_DIR = os.path.join(LIBREBASE_DIR, "data", "marketing")
SCAN_CLI = os.path.join(LIBREBASE_DIR, "librebase_competitive_scan.py")

os.environ["LIBREBASE_COMPETITIVE_DB"] = DB_PATH
os.makedirs(MARKETING_DIR, exist_ok=True)

# ── Hermes MCP endpoint ──────────────────────────────────────────────────
# The Hermes Agent desktop app runs a gateway on a localhost port.
# Find it via the kernel port file or lsof.
def find_hermes_port():
    # Check kernel session port files
    import glob
    for f in glob.glob("/var/folders/*/*/*/hermes_kernel_*/.port"):
        try:
            with open(f) as fp:
                port = int(fp.read().strip())
                print(f"[hermes] Found port {port} via {f}")
                return port
        except:
            pass
    # Check common ports
    import socket
    for p in [3000, 3100, 3200, 8080, 9000]:
        s = socket.socket()
        s.settimeout(0.3)
        if s.connect_ex(("127.0.0.1", p)) == 0:
            s.close()
            print(f"[hermes] Port {p} is open")
            return p
        s.close()
    # Fallback: check listening processes
    try:
        r = subprocess.run(["lsof", "-i", "-P", "-n"], capture_output=True, text=True, timeout=10)
        for line in r.stdout.split("\n"):
            if "LISTEN" in line and "python" in line.lower():
                parts = line.split()
                if len(parts) >= 9:
                    addr = parts[8]
                    port_str = addr.split(":")[-1]
                    try:
                        p = int(port_str)
                        print(f"[hermes] Found listening port {p}")
                        return p
                    except:
                        pass
    except:
        pass
    raise RuntimeError("Cannot find Hermes daemon port. Is Hermes Agent running?")

HERMES_PORT = find_hermes_port()
MCP_url = f"http://127.0.0.1:{HERMES_PORT}/c/tool/call"

def hermes_call(tool_name, **kwargs):
    """Call a Hermes MCP tool."""
    payload = json.dumps({"tool": tool_name, "args": kwargs}).encode()
    req = urllib.request.Request(
        MCP_url,
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"[hermes] HTTP {e.code}: {body[:200]}")
        raise
    except urllib.error.URLError as e:
        print(f"[hermes] Connection fail: {e}")
        raise

def web_search(query, limit=5):
    return hermes_call("web_search", query=query, limit=limit)

def web_extract(urls, char_limit=None):
    return hermes_call("web_extract", urls=urls, char_limit=char_limit or 15000)

# ── Trend queries ─────────────────────────────────────────────────────────
TREND_QUERIES = [
    "backend-as-a-service trends 2025 AI agents",
    "MCP server BaaS competitor wave 2025",
    "open source backend platform new features 2025",
    "serverless database edge compute developer tools 2025",
    "PostgreSQL managed service AI integration 2025",
    "real-time API backend platform comparison 2025",
    "developer tools AI agent SDK release 2025",
    "self-host Kubernetes BaaS alternative 2025",
]

# ── Classification (simplified) ──────────────────────────────────────────
FN = {
    "mcp": "mcp-agent-api", "model context protocol": "mcp-agent-api",
    "agent api": "mcp-agent-api", "agent sdk": "mcp-agent-api",
    "agent skill": "mcp-agent-api", "coding agent": "mcp-agent-api",
    "ai assistant": "mcp-agent-api", "cursor plugin": "mcp-agent-api",
    "claude code": "mcp-agent-api", "opencode": "mcp-agent-api",
    "codex": "mcp-agent-api", "antigravity": "mcp-agent-api",
    "postgres": "postgresql-db", "postgresql": "postgresql-db",
    "sql": "postgresql-db", "database": "postgresql-db",
    "managed postgres": "postgresql-db",
    "pgvector": "vector-embeddings", "vector search": "vector-embeddings",
    "embedding": "vector-embeddings", "ai extension": "vector-embeddings",
    "auth": "auth", "authentication": "auth",
    "sign in": "auth", "sign-in": "auth", "login": "auth",
    "oauth": "auth", "sso": "auth", "mfa": "auth",
    "multi-factor": "auth",
    "storage": "storage", "file storage": "storage",
    "object storage": "storage", "blob": "storage",
    "realtime": "realtime", "websocket": "realtime",
    "subscription": "realtime", "live": "realtime",
    "broadcast": "realtime",
    "self-host": "self-host", "self host": "self-host",
    "docker compose": "self-host", "docker": "self-host",
    "single binary": "self-host", "single-file": "self-host",
    "kubernetes": "kubernetes", "k8s": "kubernetes", "helm": "kubernetes",
    "edge function": "edge-functions", "serverless function": "edge-functions",
    "cloud function": "edge-functions", "lambda": "edge-functions",
    "deno": "edge-functions",
    "graphql": "graphql", "rest api": "api-changes",
    "pricing": "pricing-changes", "price": "pricing-changes",
    "plan": "pricing-changes", "tier": "pricing-changes",
    "free tier": "pricing-changes", "pro plan": "pricing-changes",
    "cost": "pricing-changes",
    "funding": "funding", "series a": "funding",
    "series b": "funding", "raise": "funding",
    "acquisition": "funding", "acquired": "funding", "invest": "funding",
    "hiring": "hiring", "we're hiring": "hiring",
    "careers": "hiring", "job": "hiring",
    "engineering team": "hiring",
    "sdk": "sdk-release", "cli": "sdk-release",
    "client library": "sdk-release", "typescript": "sdk-release",
    "python": "sdk-release", "go sdk": "sdk-release",
    "documentation": "documentation", "docs": "documentation",
    "guide": "documentation", "tutorial": "documentation",
    "how to": "documentation",
    "enterprise": "enterprise-features", "rbac": "enterprise-features",
    "audit log": "enterprise-features", "sla": "enterprise-features",
    "compliance": "enterprise-features", "security": "enterprise-features",
    "open source": "open-source", "open-source": "open-source",
    "oss": "open-source", "mit": "open-source",
    "apache": "open-source", "bsd": "open-source",
    "console": "console-studio", "dashboard": "console-studio",
    "studio": "console-studio",
    "multi-region": "multi-region", "regional": "multi-region",
    "global": "multi-region",
    "custom domain": "custom-domains", "domain": "custom-domains",
    "delete": "delete-endpoints", "crud": "delete-endpoints",
    "lifecycle": "delete-endpoints",
    "billing": "billing-plans", "usage-based": "billing-metering",
    "metering": "billing-metering", "overages": "billing-metering",
    "newsletter": "go-to-market",
    "launch": "feature-launch", "release": "feature-launch",
    "beta": "feature-launch", "preview": "feature-launch",
    "generally available": "feature-launch", "ga": "feature-launch",
    "introducing": "feature-launch", "announcing": "feature-launch",
}

SK = ["mcp", "agent api", "agent sdk", "agent skill", "model context protocol",
      "coding agent", "ai assistant", "cursor plugin",
      "vector", "embeddings", "pgvector",
      "edge function", "serverless function"]

WK = ["self-host", "single binary", "open source", "docker compose",
      "lightweight", "simple", "easy", "minimal"]

def classify(title, url):
    text = (title + " " + url).lower()
    matched = [f for k, f in FN.items() if k in text]
    if not matched:
        if any(w in text for w in ["launch", "announce", "release", "introducing"]):
            return ("feature-launch", "neutral")
        return ("general", "noise")
    feat = matched[-1]
    if any(k in text for k in SK):
        return (feat, "strong")
    if any(k in text for k in WK):
        return (feat, "weak")
    return (feat, "neutral")

def is_dup(url, conn):
    r = conn.execute("SELECT id FROM daily_scans WHERE url=? AND date(scanned_at)=date('now')", (url,)).fetchone()
    return r is not None

def get_content(url, results):
    try:
        urls = [url]
        for r in results[1:3]:
            u = r.get("url", "")
            if u and u != url:
                urls.append(u)
                break
        res = web_extract(urls=urls[:2], char_limit=3000)
        for r in res.get("results", []):
            if r.get("url") == url and not r.get("error"):
                c = r.get("content", "") or ""
                return c[:1500] if c else ""
    except:
        pass
    return ""

# ── Main scan ─────────────────────────────────────────────────────────────
print(f"[weekly-trend] LibreBase Weekly Trend Deep-Dive — {date.today().isoformat()}")
print()

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

total_findings = 0
all_findings = []

for qi, query in enumerate(TREND_QUERIES, 1):
    print(f"[{qi}/8] {query}")
    try:
        res = web_search(query, limit=5)
    except Exception as e:
        print(f"  ✗ search error: {e}")
        continue
    results = res.get("data", {}).get("web", [])
    if not results:
        print("  → no results")
        continue
    qf = 0
    for r in results[:3]:
        url = r.get("url", "")
        title = r.get("title", "")
        snippet = r.get("description", "")
        if not url or not title:
            continue
        if is_dup(url, conn):
            continue
        feat, impact = classify(title, url)
        if impact == "noise":
            continue
        content = get_content(url, results)
        finding = {
            "competitor": "General trend" if impact != "new-competitor" else "new",
            "competitor_url": url,
            "query": query,
            "headline": title[:200],
            "url": url,
            "announced_feature": feat,
            "impact": impact,
            "librebase_delta": "",
            "raw_snippet": snippet[:500],
            "content_excerpt": content,
            "confidence": 0.65,
        }
        all_findings.append(finding)
        qf += 1
        total_findings += 1
        icon = {"strong": "🔴", "weak": "🟢", "neutral": "⚪"}.get(impact, "·")
        print(f"  {icon} [{impact:7s}] {feat:20s} | {title[:80]}")
    print(f"  → {qf} findings")
    print()

conn.close()

print("!=" * 60)
print(f"TOTAL: {total_findings} trend findings")

# ── Strong signals ────────────────────────────────────────────────────────
strong = [f for f in all_findings if f["impact"] == "strong"]
if strong:
    print(f"\n⚡ STRONG SIGNALS ({len(strong)})")
    al = []
    for sf in strong[:20]:
        al.append(f"[{sf['competitor']}] {sf['headline']}")
        al.append(f"  Feature: {sf['announced_feature']} | Conf: {sf['confidence']:.0%}")
        if sf["url"]: al.append(f"  URL: {sf['url']}")
        al.append(f"  Snippet: {sf['raw_snippet'][:200]}")
        al.append("")
    atxt = "\n".join(al)
    print(atxt)
    ap = os.path.join(MARKETING_DIR, f"strong_alerts_{date.today().isoformat()}.md")
    with open(ap, "w") as fh:
        fh.write(f"# LibreBase Strong Signal Alerts — {date.today().isoformat()}\n\n")
        fh.write(f"**{len(strong)} strong signals detected.**\n\n")
        fh.write(atxt)
    print(f"→ alerts: {ap}")

# ── Persist ──────────────────────────────────────────────────────────────
print("\n· Persisting...")
fj = json.dumps(all_findings)
pr = subprocess.run([sys.executable, SCAN_CLI], input=fj, capture_output=True, text=True, cwd=LIBREBASE_DIR)
if pr.returncode == 0:
    st = json.loads(pr.stdout)
    print(f"  ✓ {json.dumps(st, indent=2)}")
else:
    print(f"  ✗ error: {pr.stderr}")

print("\n· Digest...")
dp = subprocess.run([sys.executable, SCAN_CLI, "--digest"], capture_output=True, text=True, cwd=LIBREBASE_DIR)
if dp.returncode == 0:
    dpath = os.path.join(MARKETING_DIR, f"competitive_digest_{date.today().isoformat()}.md")
    with open(dpath, "w") as fh:
        fh.write(dp.stdout)
    print(f"  ✓ digest: {dpath}")
    print()
    print(dp.stdout)
else:
    print(f"  ✗ digest error: {dp.stderr}")

result = {
    "findings": total_findings,
    "strong_signals": len(strong),
    "queries": len(TREND_QUERIES),
    "digest_file": os.path.join(MARKETING_DIR, f"competitive_digest_{date.today().isoformat()}.md"),
    "alerts_file": os.path.join(MARKETING_DIR, f"strong_alerts_{date.today().isoformat()}.md") if strong else None,
}
print(f"\nDone: {json.dumps(result, indent=2)}")
