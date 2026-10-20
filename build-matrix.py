#!/usr/bin/env python3
"""Build the LibreBase integration matrix HTML from librebase_competitive.db."""
import sqlite3

db_path = "/Users/julian/Documents/coding-projects/librebase/librebase_competitive.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

integration_features = [
    ("webhooks", "webhooks"),
    ("slack-integration", "slack-integration"),
    ("observability-logging", "observability-logging"),
    ("ci-cd-integration", "ci-cd-integration"),
    ("marketplace-extensibility", "marketplace-extensibility"),
    ("billing-usage-metering", "billing-usage-metering"),
    ("github-issues-sync", "github-issues-sync"),
    ("serverless-functions", "serverless-functions"),
    ("sso-saml", "sso-saml"),
    ("multi-region-active-active", "multi-region-active-active"),
    ("partner-agent-auth", "partner-agent-auth"),
]

display_names = [d[0] for d in integration_features]
display_headers = [
    "webhooks",
    "slack-integration",
    "observability / logging",
    "ci-cd hooks",
    "partner marketplace",
    "billing usage-metering",
    "github-issues-sync",
    "edge-functions / serverless",
    "SSO SAML",
    "multi-region active-active",
    "partner-agent-auth",
]

db_features = [d[1] for d in integration_features]

our_scores = {}
our_details = {}
for db_f, _ in integration_features:
    cur.execute(
        "SELECT our_offer, strength FROM our_positioning WHERE feature = ?", (db_f,)
    )
    r = cur.fetchone()
    if r:
        our_details[db_f] = r[0]
        our_scores[db_f] = 2 if r[1] == "strong" else (1 if r[1] == "neutral" else 0)
    else:
        our_details[db_f] = "Not yet positioned."
        our_scores[db_f] = 0

cur.execute("SELECT id, name, category FROM competitors ORDER BY name")
competitors = cur.fetchall()

matrix = []
for cid, cname, cat in competitors:
    row = {"id": cid, "name": cname, "category": cat, "scores": {}}
    for db_f in db_features:
        cur.execute(
            "SELECT offered, detail FROM competitor_features WHERE competitor_id = ? AND feature = ?",
            (cid, db_f)
        )
        r = cur.fetchone()
        row["scores"][db_f] = r[0] if r else 0
    matrix.append(row)

conn.close()

# Build HTML
parts = []
parts.append("""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>LibreBase — Integration Matrix</title>
<style>
  :root {
    --bg: #0f172a; --card: #1e293b; --text: #e2e8f0;
    --muted: #94a3b8; --accent: #38bdf8;
    --green: #4ade80; --amber: #fbbf24; --red: #f87171; --border: #334155;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: var(--bg); color: var(--text); padding: 24px; min-width: 1200px;
  }
  h1 { font-size: 24px; margin-bottom: 4px; }
  .subtitle { color: var(--muted); font-size: 13px; margin-bottom: 20px; line-height: 1.5; }
  .controls { display: flex; gap: 12px; margin-bottom: 16px; flex-wrap: wrap; align-items: center; }
  select, button {
    background: var(--card); color: var(--text);
    border: 1px solid var(--border); padding: 6px 12px;
    border-radius: 6px; font-size: 13px; cursor: pointer;
  }
  select:focus, button:focus { outline: 2px solid var(--accent); outline-offset: 2px; }
  .matrix-wrap { overflow-x: auto; border: 1px solid var(--border); border-radius: 8px; background: var(--card); }
  table { border-collapse: collapse; width: 100%; font-size: 12px; }
  th, td { text-align: center; padding: 6px 8px; border-bottom: 1px solid var(--border); white-space: nowrap; }
  th { background: #0f172a; color: var(--muted); font-weight: 600; font-size: 10px; position: sticky; top: 0; }
  td { cursor: default; }
  th:first-child, td:first-child { text-align: left; padding-left: 12px; }
  .comp-name { font-weight: 600; font-size: 12px; }
  .comp-cat { color: var(--muted); font-size: 10px; text-align: left; padding-left: 12px; }
  .feature-col { min-width: 90px; }
  .score-cell { width: 32px; font-weight: 700; font-size: 12px; }
  .score-2 { color: var(--green); }
  .score-1 { color: var(--amber); }
  .score-0 { color: var(--muted); }
  .highlight-row td { background: rgba(56,189,248,0.06); font-weight: 600; }
  .legend { display: flex; gap: 16px; margin-top: 12px; font-size: 12px; color: var(--muted); flex-wrap: wrap; }
  .legend-item { display: flex; align-items: center; gap: 4px; }
  .legend-swatch { width: 16px; height: 16px; border-radius: 3px; }
  .swatch-2 { background: rgba(74,222,128,0.2); border: 1px solid var(--green); }
  .swatch-1 { background: rgba(251,191,36,0.2); border: 1px solid var(--amber); }
  .swatch-0 { background: transparent; border: 1px solid var(--border); }
  .summary { margin-top: 20px; border-top: 1px solid var(--border); padding-top: 16px; }
  .summary h2 { font-size: 16px; margin-bottom: 8px; }
  .summary p { font-size: 13px; color: var(--muted); margin-bottom: 4px; line-height: 1.5; max-width: 800px; }
  .total-bar { display: flex; gap: 16px; margin-top: 12px; flex-wrap: wrap; }
  .total-item { font-size: 13px; }
  .total-num { font-weight: 700; color: var(--accent); }
  .header-row { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px; gap: 12px; flex-wrap: wrap; }
  .last-updated { font-size: 11px; color: var(--muted); }
  .gap-count { color: var(--red); font-size: 10px; margin-left: 4px; }
</style>
</head>
<body>
<div class="header-row">
  <div>
    <h1>LibreBase — Integration Gap Matrix</h1>
    <p class="subtitle">11 integration dimensions × 34 competitors. Score: <span style="color:var(--green)">✓✓ = fully offered</span>, <span style="color:var(--amber)">✓ = partial / limited</span>, <span style="color:var(--muted)">✗ = not offered</span>. LibreBase row is our current positioning — the rest is the competitive landscape.</p>
  </div>
  <div class="last-updated">Source: librebase_competitive.db · 2026-08-29</div>
</div>
<div class="controls">
  <select id="catFilter">
    <option value="all">All categories</option>
""")

for cat in sorted(set(m["category"] for m in matrix)):
    parts.append(f'    <option value="{cat}">{cat}</option>\n')

parts.append("""  </select>
  <button id="resetView">Reset</button>
  <span style="font-size:11px;color:var(--muted);">Filter by category (LibreBase row always visible)</span>
</div>
<div class="matrix-wrap">
<table>
<thead>
<tr>
  <th style="min-width:160px;">Competitor</th>
""")

for hdr in display_headers:
    parts.append(f'  <th class="feature-col">{hdr}</th>\n')

parts.append("""</tr>
</thead>
<tbody>
""")

# LibreBase row
parts.append('<tr class="highlight-row">\n')
parts.append('  <td class="comp-name">LibreBase <span style="font-weight:400;color:var(--accent);">(us)</span></td>\n')
for db_f in db_features:
    sc = our_scores[db_f]
    cls = "score-2" if sc == 2 else ("score-1" if sc == 1 else "score-0")
    label = "✓✓" if sc == 2 else ("✓" if sc == 1 else "✗")
    parts.append(f'  <td class="score-cell {cls}">{label}</td>\n')
parts.append('</tr>\n')

# Competitor rows
for comp in matrix:
    parts.append('<tr>\n')
    parts.append(f'  <td class="comp-name">{comp["name"]}</td>\n')
    parts.append(f'  <td class="comp-cat">{comp["category"]}</td>\n')
    for db_f in db_features:
        sc = comp["scores"][db_f]
        cls = "score-2" if sc == 2 else ("score-1" if sc == 1 else "score-0")
        label = "✓✓" if sc == 2 else ("✓" if sc == 1 else "✗")
        parts.append(f'  <td class="score-cell {cls}">{label}</td>\n')
    parts.append('</tr>\n')

parts.append("""</tbody>
</table>
</div>
<div class="legend">
  <div class="legend-item"><div class="legend-swatch swatch-2"></div> <strong>✓✓ = fully offered</strong></div>
  <div class="legend-item"><div class="legend-swatch swatch-1"></div> <strong>✓ = partial / limited</strong></div>
  <div class="legend-item"><div class="legend-swatch swatch-0"></div> <strong>✗ = not offered</strong></div>
  <div class="legend-item" style="margin-left:auto;">Max score per competitor: 22 (11 × 2)</div>
</div>
<div class="summary">
<h2>LibreBase positioning — all 11 integration dimensions currently weak</h2>
""")

for db_f, dn in integration_features:
    detail = our_details[db_f]
    parts.append(f'<p><strong>{dn}</strong> — {detail[:120]}</p>\n')

parts.append("""</div>
<div class="summary">
<h2>Competitor coverage (11 dimensions, max 22)</h2>
<div class="total-bar">
""")

totals = []
for comp in matrix:
    total = sum(comp["scores"][db_f] for db_f in db_features)
    gaps = sum(1 for db_f in db_features if comp["scores"][db_f] == 0)
    totals.append((comp["name"], comp["category"], total, gaps))

totals.sort(key=lambda x: (-x[2], x[0]))

for name, cat, total, gaps in totals:
    cov = "✓" if gaps == 0 else f"{gaps} gap{'s' if gaps != 1 else ''}"
    parts.append(f'<div class="total-item"><strong>{name}</strong> <span style="color:var(--muted);font-size:11px;">({cat})</span> — <span class="total-num">{total}/22</span> <span class="gap-count">{cov}</span></div>\n')

parts.append("""</div>
</div>
<script>
const catFilter = document.getElementById('catFilter');
const resetBtn = document.getElementById('resetView');
function filterRows(category) {
  document.querySelectorAll('tbody tr').forEach(row => {
    const nameEl = row.querySelector('.comp-name');
    if (!nameEl) { row.style.display = ''; return; }
    const name = nameEl.textContent;
    if (name.includes('LibreBase')) { row.style.display = ''; return; }
    const cat = row.querySelector('.comp-cat');
    if (!cat) { row.style.display = ''; return; }
    row.style.display = cat.textContent === category ? '' : 'none';
  });
}
catFilter.addEventListener('change', () => filterRows(catFilter.value));
resetBtn.addEventListener('click', () => { catFilter.value = 'all'; filterRows('all'); });
</script>
</body>
</html>
""")

html = "".join(parts)
output_path = "/Users/julian/Documents/coding-projects/librebase/docs/integration-matrix.html"
with open(output_path, "w") as f:
    f.write(html)

print(f"Wrote {output_path} ({len(html)} bytes)")
print(f"\nTop 5 by coverage (11 integration dimensions):")
for name, cat, total, gaps in totals[:5]:
    print(f"  {name:20s} ({cat:12s}) — {total}/22, {gaps} gap{'s' if gaps != 1 else ''}")
print(f"\nBottom 5:")
for name, cat, total, gaps in totals[-5:]:
    print(f"  {name:20s} ({cat:12s}) — {total}/22, {gaps} gap{'s' if gaps != 1 else ''}")
print(f"\nLibreBase — 0/22 (all 11 gaps = our positioning)")
