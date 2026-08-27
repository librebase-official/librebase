#!/usr/bin/env python3
"""
LibreBase branded market-research PDF — HTML→Chromium headless print.
Uses the exact same brand as librebase.xyz: dark ink bg, teal accent, Orbitron/Space Grotesk/IBM Plex Mono.
"""
import os, sys, subprocess, tempfile, shutil

FONT_DIR = "/Users/julian/Library/Fonts"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

OUTPUT_PATH = "/Users/julian/Documents/coding-projects/librebase/docs/librebase-market-research-brief.pdf"

# ═══════════════════════════════════════════
#  LIBREBASE BRAND TOKENS
# ═══════════════════════════════════════════
INK     = "#071014"   # --lb-ink
PANEL   = "#0E1A1C"   # --lb-panel
FOG     = "#9BB0AA"   # --lb-fog
PAPER   = "#E7F2EC"   # --lb-paper  
SIGNAL  = "#2FD4C2"   # --lb-signal  teal accent
SIGNALD = "#1FA89A"   # --lb-signal-dim
WARN    = "#E8A838"   # --lb-warn
BORDER  = "#2D3A4D"   # --border
LINE    = "rgba(231,242,236,0.12)"  # --lb-line
RADIUS  = "8px"

ORBITRON  = "'Orbitron', sans-serif"
SPACE_GROtesk = "'Space Grotesk', sans-serif"
IBM_PLEX  = "'IBM Plex Mono', monospace"


def brand_css():
    return f"""
@page {{
  size: A4;
  margin: 20mm 18mm 22mm 18mm;
  @top-left {{
    content: "LibreBase Market Research Brief — Internal  |  August 2026";
    font-family: {IBM_PLEX};
    font-size: 7pt;
    color: {FOG};
  }}
  @top-right {{
    content: "";
  }}
  @bottom-left {{
    content: "LibreBase  ·  librebase.xyz";
    font-family: {IBM_PLEX};
    font-size: 7.5pt;
    color: {FOG};
  }}
  @bottom-center {{
    content: "Confidential — Internal Research";
    font-family: {IBM_PLEX};
    font-size: 7.5pt;
    color: {FOG};
  }}
  @bottom-right {{
    content: "Page " counter(page) " of " counter(pages);
    font-family: {IBM_PLEX};
    font-size: 7.5pt;
    color: {FOG};
  }}
}}

* {{ box-sizing: border-box; }}

html, body {{
  margin: 0;
  padding: 0;
  background: {INK};
  color: {PAPER};
  font-family: {SPACE_GROtesk};
  font-size: 9.5pt;
  line-height: 1.55;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}}

/* ── Typography ── */
.orbitron {{ font-family: {ORBITRON}; }}
.serif {{ font-family: {SPACE_GROtesk}; }}
.mono   {{ font-family: {IBM_PLEX}; }}

h1, h2, h3, h4, .heading {{
  font-family: {ORBITRON};
  color: {PAPER};
  font-weight: 600;
  letter-spacing: -0.02em;
}}

h1 {{ font-size: 20pt; margin: 0 0 6pt 0; }}
h2 {{ font-size: 13pt; margin: 12pt 0 4pt 0; }}
h3 {{ font-size: 10.5pt; margin: 8pt 0 3pt 0; color: {SIGNAL}; }}

p {{ margin: 0 0 5pt 0; color: {PAPER}; }}
p.muted {{ color: {FOG}; font-size: 8.5pt; }}

a {{ color: {SIGNAL}; text-decoration: none; }}

/* ── Layout ── */
.page {{ padding: 0; }}
.section {{ margin-bottom: 16pt; }}
.section-title {{
  font-family: {ORBITRON};
  font-size: 15pt;
  font-weight: 600;
  color: {PAPER};
  margin: 0 0 4pt 0;
  padding-bottom: 3pt;
  border-bottom: 2px solid {SIGNAL};
  display: inline-block;
  letter-spacing: -0.02em;
}}
.section-subtitle {{
  font-size: 9pt;
  color: {FOG};
  margin: 0 0 8pt 0;
}}

/* ── Brand bar (top of page, like landing) ── */
.brand-bar {{
  display: flex;
  height: 3.5pt;
  margin: 0;
  width: 100%;
}}
.brand-bar .deep {{ flex: 0 0 58%; background: {INK}; }}
.brand-bar .mid  {{ flex: 0 0 12%; background: {SIGNAL}; }}
.brand-bar .rest {{ flex: 1;    background: {SIGNALD}; opacity: 0.6; }}

/* ── Cover / title block ── */
.cover {{
  margin-bottom: 18pt;
}}
.cover-logo {{
  display: inline-flex;
  align-items: center;
  gap: 8pt;
  margin-bottom: 10pt;
}}
.cover-logo .lb-box {{
  width: 38pt;
  height: 38pt;
  background: {INK};
  border-radius: {RADIUS};
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}}
.cover-logo .lb-box .mid {{ position: absolute; bottom: 0; left: 0; right: 0; height: 50%; background: {SIGNAL}; }}
.cover-logo .lb-box .accent {{ position: absolute; top: 50%; left: 0; height: 50%; width: 50%; background: {WARN}; }}
.cover-logo .lb-box span {{
  font-family: {ORBITRON};
  font-size: 18pt;
  font-weight: 700;
  color: {PAPER};
  position: relative;
  z-index: 1;
}}
.cover-tag {{
  font-family: {IBM_PLEX};
  font-size: 8pt;
  color: {FOG};
  letter-spacing: 0.08em;
  text-transform: uppercase;
}}
.cover-title {{
  font-family: {ORBITRON};
  font-size: 26pt;
  font-weight: 700;
  color: {PAPER};
  letter-spacing: -0.02em;
  margin: 6pt 0 2pt 0;
}}
.cover-sub {{
  font-family: {SPACE_GROtesk};
  font-size: 14pt;
  color: {SIGNAL};
  margin: 0 0 8pt 0;
}}
.cover-meta {{
  font-family: {IBM_PLEX};
  font-size: 8.5pt;
  color: {FOG};
  margin: 8pt 0 0 0;
  line-height: 1.6;
}}
.cover-meta strong {{ color: {PAPER}; }}

/* ── Insight / callout boxes ── */
.callout {{
  background: {PANEL};
  border-left: 3.5pt solid {SIGNAL};
  border-radius: {RADIUS};
  padding: 8pt 10pt;
  margin: 10pt 0;
}}
.callout-red {{
  background: rgba(198,40,40,0.08);
  border-left: 3.5pt solid {WARN};
  border-radius: {RADIUS};
  padding: 8pt 10pt;
  margin: 10pt 0;
}}
.callout-green {{
  background: rgba(46,125,50,0.08);
  border-left: 3.5pt solid {SIGNAL};
  border-radius: {RADIUS};
  padding: 8pt 10pt;
  margin: 10pt 0;
}}
.callout-label {{
  font-family: {ORBITRON};
  font-size: 9pt;
  font-weight: 600;
  color: {SIGNAL};
  letter-spacing: 0.04em;
  text-transform: uppercase;
  margin-bottom: 3pt;
}}
.callout-red .callout-label {{ color: {WARN}; }}
.callout-green .callout-label {{ color: {SIGNAL}; }}

/* ── Tables ── */
table {{
  width: 100%;
  border-collapse: collapse;
  margin: 8pt 0;
  font-size: 8.5pt;
}}
thead th {{
  background: {PANEL};
  color: {SIGNAL};
  font-family: {ORBITRON};
  font-size: 8pt;
  font-weight: 600;
  padding: 5pt 6pt;
  text-align: left;
  border-bottom: 1.5pt solid {SIGNAL};
  letter-spacing: 0.02em;
}}
tbody td {{
  padding: 4pt 6pt;
  color: {PAPER};
  border-bottom: 0.5pt solid {BORDER};
  vertical-align: top;
}}
tbody tr:nth-child(even) td {{
  background: {PANEL};
}}
tbody tr:nth-child(odd) td {{
  background: rgba(7,16,20,0.4);
}}
td.metric {{ font-weight: 600; color: {PAPER}; }}
td.value {{ color: {SIGNAL}; font-weight: 600; font-family: {IBM_PLEX}; }}
td.muted {{ color: {FOG}; }}

/* ── Bullet lists ── */
ul {{
  margin: 4pt 0;
  padding-left: 14pt;
}}
ul li {{
  margin-bottom: 3pt;
  color: {PAPER};
  line-height: 1.45;
}}
ul li b {{ color: {PAPER}; }}
ul li .accent {{ color: {SIGNAL}; }}

/* ── Subsection headings ── */
.subhead {{
  font-family: {ORBITRON};
  font-size: 10pt;
  color: {PAPER};
  margin: 8pt 0 2pt 0;
  border-left: 2pt solid {SIGNAL};
  padding-left: 6pt;
}}

/* ── Two-column layout for summary ── */
.cols {{ display: flex; gap: 12pt; }}
.col {{ flex: 1; }}

/* ── Sources / footnotes ── */
.sources {{
  margin-top: 16pt;
  padding-top: 6pt;
  border-top: 0.5pt solid {BORDER};
  font-family: {IBM_PLEX};
  font-size: 7.5pt;
  color: {FOG};
  line-height: 1.5;
  font-style: italic;
}}

/* ── Page break helper ── */
.page-break {{ page-break-before: always; }}

/* ── Teal accent dot for bullets ── */
.bullet-dot {{
  display: inline-block;
  width: 5pt;
  height: 5pt;
  background: {SIGNAL};
  border-radius: 50%;
  margin-right: 5pt;
  vertical-align: middle;
}}
"""


def build_html():
    """Return full HTML string for the research brief."""
    sections = []

    # ── COVER ──
    sections.append(f"""
<div class="cover">
  <div class="cover-logo">
    <div class="lb-box"><div class="mid"></div><div class="accent"></div>
      <span>LB</span></div>
    <span class="cover-tag">Internal Research Brief · For Sales Use Only</span>
  </div>
  <div class="cover-title">LibreBase Market Intelligence</div>
  <div class="cover-sub">Sample Library &amp; AI Music Tools Landscape</div>
  <div style="height:2.5pt; background:{SIGNAL}; margin: 8pt 0 6pt 0; width: 200pt; border-radius: 2pt;"></div>
  <div class="cover-meta">
    <strong>Prepared for:</strong> Sales Representative — Internal Use<br>
    <strong>Date:</strong> August 16–18, 2026 &nbsp;&nbsp;·&nbsp;&nbsp;
    <strong>Classification:</strong> Confidential
  </div>
  <div class="brand-bar" style="margin-top:14pt;">
    <div class="deep"></div><div class="mid"></div><div class="rest"></div>
  </div>
</div>
""")

    # ── 1. EXECUTIVE SUMMARY ──
    sections.append("""
<div class="section">
  <h2 class="section-title">1. Executive Summary</h2>
  <p>This brief consolidates three research streams into a single sales-ready reference:
    <strong>Sample Marketplace &amp; Subscription Services</strong>,
    <strong>AI-Powered Sample Generators &amp; ML Music Tools</strong>, and
    <strong>Traditional Sample Library Competitors</strong>. Together they map the full competitive
    terrain for music production sampling — the <strong>$1.8B</strong> sector where LibreBase positions
    its open-knowledge angle against entrenched incumbents.</p>

  <div class="callout">
    <div class="callout-label">The One-Line Pitch</div>
    The sample market is <strong>$1.8B</strong> and growing at <strong>8.9–9.5% CAGR</strong>. Splice
    (<strong>22% share</strong>, 6M+ users) dominates volume; Loopcloud owns DAW integration; Tracklib
    monopolises legal clearance. But every incumbent charges subscription rents that producers hate,
    hides quality behind credit systems, and lacks any all-in-one AI-native workflow.
    <strong>The gap is real — and wide.</strong>
  </div>

  <h3 style="margin-top:10pt;">Why This Matters for Sales</h3>
  <ul>
    <li><span class="bullet-dot"></span><strong>Mid-market is underserved.</strong> Enterprise tools
      (Sphera, Enablon) cost six figures; consumer subs ($8–40/mo) feel predatory. The
      <strong>$150–300 "professional-lite"</strong> tier is empty.</li>
    <li><span class="bullet-dot"></span><strong>AI is the wedge, not the product.</strong> Every
      competitor's AI is bolted-on and mediocre. The gap: a tool that unifies generation + separation
      + editing + MIDI in one plugin.</li>
    <li><span class="bullet-dot"></span><strong>Perpetual ownership is the emotional hook.</strong>
      "Cancel = lose everything" is the #1 pain point across Splice, Loopcloud, Output, EastWest. A
      hybrid ownership model is unclaimed territory.</li>
    <li><span class="bullet-dot"></span><strong>Consolidation breeds vulnerability.</strong> Splice
      owns Spitfire, Output, Sample Magic. Users are anxious; a vendor-neutral, open platform is a
      natural trust alternative.</li>
  </ul>
</div>
""")

    # ── 2. MARKET SNAPSHOT ──
    market_rows = [
        ("Market size (2025)", "$1.8B", "Large enough to matter; not saturated"),
        ("Projected (2034)", "$3.9–4.6B", "~9% CAGR — sustained growth, not a bubble"),
        ("Splice market share", "~22%", "Leading, but not a monopoly"),
        ("Splice registered users", "6M+", "Huge installed base — churn opportunity"),
        ("Splice 2024 downloads", "~350M", 'Scale, but "generic" quality complaints'),
        ("Spotify-for-samples sentiment", "Broken", "Ownership is the untapped wedge"),
        ("AI sample gen market", "Fragmented", "No dominant all-in-one — white space"),
        ("SDS/Compliance adj. market", "$1.34B → $2.49B (14% CAGR)",
         "Parallel vertical with same open-data angle"),
    ]
    rows_html = "\n".join(
        f"<tr><td class='metric'>{m}</td><td class='value'>{v}</td><td class='muted'>{s}</td></tr>"
        for m, v, s in market_rows
    )
    sections.append(f"""
<div class="section">
  <h2 class="section-title">2. Market Snapshot</h2>
  <table>
    <thead><tr><th>Metric</th><th>Value</th><th>Sales Signal</th></tr></thead>
    <tbody>{rows_html}</tbody>
  </table>
</div>
""")

    # ── 3. COMPETITIVE LANDSCAPE ──
    sections.append("""
<div class="section">
  <h2 class="section-title">3. Competitive Landscape — Subscription Platforms</h2>

  <h3 class="subhead">Splice — The Incumbent Leader</h3>
  <ul>
    <li><span class="bullet-dot"></span><strong>Library:</strong> 3–4M+ samples.
      <strong>Pricing:</strong> Sounds+ $12.99/mo, Creator $19.99/mo, Creator+ $39.99/mo;
      annual Creator promo at $120/yr.</li>
    <li><span class="bullet-dot"></span><strong>Strengths:</strong> Largest library, brand recognition,
      AI search, Rent-to-Own, Splice Studio. Acquired Spitfire Audio ($50M, 2025) + Output +
      Sample Magic — consolidation king.</li>
    <li><span class="bullet-dot"></span><strong>Weaknesses:</strong> Credit system feels restrictive;
      price hikes controversial (Sounds 1000 → $34.99/mo); lose access on cancel; credits expire.
      80% of samples criticised as "generic" or "samey".</li>
  </ul>

  <h3 class="subhead">Loopcloud — The DAW Integration Leader</h3>
  <ul>
    <li><span class="bullet-dot"></span><strong>Library:</strong> 4M+ samples.
      <strong>Pricing:</strong> Artist $7.99/mo, Studio $11.99/mo (most popular), Professional tier.</li>
    <li><span class="bullet-dot"></span><strong>Strengths:</strong> Deepest DAW integration
      (VST/AAX/AU plugin), no credit limits (points-based packs), best for house/techno, cloud
      storage (10–50GB+), AI-assisted browsing, time-stretch/pitch-shift in-plugin, daily free sounds.</li>
    <li><span class="bullet-dot"></span><strong>Weaknesses:</strong> Internet required for cloud features;
      plugin learning curve; library overlap with Splice.</li>
  </ul>

  <h3 class="subhead">Tracklib — The Legal Clearance Monopoly</h3>
  <ul>
    <li><span class="bullet-dot"></span><strong>Library:</strong> Original songs (not royalty-free loops).
      <strong>Pricing:</strong> Lite $8.99/mo, Premium $13.99/mo, Max $19.99/mo.</li>
    <li><span class="bullet-dot"></span><strong>Strengths:</strong> One-of-a-kind — real records legally
      sampleable; used by Kendrick Lamar producers; no upfront licensing fees; drag-to-DAW desktop app.</li>
    <li><span class="bullet-dot"></span><strong>Weaknesses:</strong> No free account (must pay to start);
      Trustpilot 2.0/5; confusing tier structure (A/B/C clearance); limited royalty-free genres.</li>
  </ul>

  <h3 class="subhead">The Rest: Noiiz, BandLab, Output, LANDR</h3>
  <table>
    <thead><tr><th>Platform</th><th>Model</th><th>Price</th><th>Watch</th></tr></thead>
    <tbody>
      <tr><td class="metric">Noiiz</td><td>Unlimited downloads</td><td class="value">$5–$10/mo; $99/yr</td><td class="muted">Simple pricing but small library; Trustpilot 2.2/5</td></tr>
      <tr><td class="metric">BandLab</td><td>Social creation</td><td class="value">Free / $8.25–$16/mo</td><td class="muted">Dark horse — pulls Gen Z with 20 free samples/mo + social</td></tr>
      <tr><td class="metric">Output Arcade</td><td>Playable sampler</td><td class="value">$9.99–$12.99/mo</td><td class="muted">Subscription-only; acquired by Splice (trust anxiety); Trustpilot 3.7/5</td></tr>
      <tr><td class="metric">Output One</td><td>Full suite</td><td class="value">$14.99/mo</td><td class="muted">Arcade + FX + Co-Producer AI — but locked to ecosystem</td></tr>
      <tr><td class="metric">LANDR Studio</td><td>Bundled</td><td class="value">$8.25–$19.99/mo</td><td class="muted">Samples + mastering + distribution — bundle play</td></tr>
      <tr><td class="metric">Sample Focus</td><td>Community</td><td class="value">Free (3 cr/wk) / Premium</td><td class="muted">Free-first model; community-curated</td></tr>
      <tr><td class="metric">NI Sounds.com</td><td>Sound design</td><td class="value">$9.99/mo</td><td class="muted">Best for ambient/experimental; niche</td></tr>
      <tr><td class="metric">Waves ILLUGEN</td><td>Text-to-sample</td><td class="value">One-time/sub</td><td class="muted">AI generator; MusicTech rated 5/10 — quality concerns</td></tr>
    </tbody>
  </table>
</div>
""")

    # ── 4. AI TOOLS DEEP DIVE ──
    ai_rows = [
        ("Samplab (RIP)", "✓", "✓", "✓", "✓", "VST3", "$12/mo"),
        ("RipX DAW", "—", "✓", "✓", "✓", "Standalone", "$60–$149 one-time"),
        ("Waves ILLUGEN", "✓", "—", "—", "—", "Standalone", "$8–$20/mo"),
        ("Text-to-Sample", "✓", "—", "—", "—", "VST3/AU", "Pay-per-use"),
        ("Magenta (Google)", "✓", "—", "—", "—", "Open", "Free"),
        ("Splice Create", "✓", "—", "—", "—", "Web", "$13/mo (credits)"),
        ("Loudly", "✓", "✓", "—", "—", "Web", "Freemium"),
        ("NeuralNote", "—", "—", "✓", "—", "VST3/AU", "Free"),
        ("Emergence Audio", "—", "—", "—", "—", "Kontakt", "$29–$1,299"),
        ("Adobe Podcast", "—", "✓", "—", "—", "Web", "Free/Premium"),
        ("BandLab", "✓", "—", "—", "—", "Web", "Free/$8–$16/mo"),
    ]
    ai_cells = ""
    for r in ai_rows:
        cells = ""
        for c in r:
            cls = ""
            color = ""
            if c == "✓":
                cls = ' style="color:' + SIGNAL + ';"'
            elif c == "—":
                cls = ' style="color:' + FOG + '; opacity:0.5;"'
            cells += f"<td{cls}>{c}</td>"
        ai_cells += f"<tr><td class='metric'>{r[0]}</td>{cells}<td class='value'>{r[5]}</td><td class='muted'>{r[6]}</td></tr>"

    sections.append(f"""
<div class="section">
  <h2 class="section-title">4. AI-Powered Sample Generators — The Emerging Layer</h2>
  <p><strong>Scope:</strong> Tools for AI/ML sample generation, stem separation, audio-to-MIDI,
     note-level editing, and transformation — August 2026 snapshot.</p>

  <div class="callout">
    <div class="callout-label">The Headline</div>
    The AI sample generation space is <strong>fragmented</strong> with no dominant all-in-one solution.
    Samplab's shutdown (<strong>Sept 17, 2026</strong>) leaves a real gap in polyphonic audio editing.
    The most promising free options (Magenta, NeuralNote) require technical skill; paid options each
    solve only part of the puzzle. <strong>The opportunity: a single plugin unifying generation +
    separation + editing + MIDI with DAW integration.</strong>
  </div>

  <h3 class="subhead">Quality Matrix</h3>
  <table>
    <thead><tr><th>Tool</th><th>AI Gen</th><th>Sep.</th><th>A2MIDI</th><th>Note Edit</th><th>Plugin</th><th>Price</th></tr></thead>
    <tbody>{ai_cells}</tbody>
  </table>

  <h3 class="subhead">Primary AI Players</h3>
  <p><strong>Samplab — Shutting Down Sept 17, 2026.</strong> Polyphonic audio-to-MIDI, stem
    separation, chord detection, note-level editing, TextToSample. Was the only tool doing note-level
    editing inside polyphonic audio seamlessly. No successor. <strong>Gap left behind:</strong> the
    biggest hole in the market.</p>
  <p><strong>Waves ILLUGEN — Text-to-Sound.</strong> Text → one-shots, loops, SFX. Standalone desktop
    app only — no plugin. Credit-based. New; MusicTech rated 5/10. Quality concerns.</p>
  <p><strong>Text-to-Sample.com — New Entrant.</strong> Text → audio (5–30s). Web + VST3/AU plugin.
    Credit-based, pay-as-you-go. No vocals. Short max length. Unproven.</p>
  <p><strong>Splice Create — April 2026 Launch.</strong> Three generative AI tools for reshaping Splice
    library sounds. Text-to-sample within Splice ecosystem. Integrated with credit system. Locked to
    Splice. Quality unproven.</p>
  <p><strong>Google Magenta — Open Source, Free.</strong> Magenta RealTime 2 (800M param transformer,
    190k hours stock music training, released June 2025). Magenta Studio for Ableton. DDSP-VST for
    realtime morphing. NSynth for neural synthesis. Requires technical setup. Research-grade, not a
    polished product.</p>
  <p><strong>RipX DAW — The Samplab Replacement (Partial).</strong> 6+ stem AI separation, note-level
    extraction/editing, instrument replacement. One-time purchase ($60–$149). Steep learning curve. Not
    a sample generator — separation + editing only.</p>

  <h3 class="subhead">Gaps in the AI Layer</h3>
  <div class="callout-green">
    <div class="callout-label">Opportunity Gaps</div>
    <ul style="margin:2pt 0;">
      <li><span class="bullet-dot"></span><strong>Polyphonic note editing void</strong> — Samplab's
        shutdown leaves the single biggest gap.</li>
      <li><span class="bullet-dot"></span><strong>No all-in-one tool</strong> — generation + separation +
        audio-to-MIDI + note editing + plugin integration: none exists.</li>
      <li><span class="bullet-dot"></span><strong>AI vocals underdeveloped</strong> — every generator
        says "instrumental only." Wide-open gap.</li>
      <li><span class="bullet-dot"></span><strong>Real-time performance tools</strong> — Magenta MRT2 and
        DDSP-VST are research-grade.</li>
      <li><span class="bullet-dot"></span><strong>Plugin integration gap</strong> — most generators are
        web-only or standalone apps.</li>
      <li><span class="bullet-dot"></span><strong>Orchestral/world instruments</strong> — AI generation of
        realistic orchestral samples remains poor.</li>
    </ul>
  </div>
</div>
""")

    # ── PAGE BREAK ──
    sections.append('<div class="page-break"></div>')

    # ── 5. TRADITIONAL LIBRARIES ──
    trad_rows = [
        ("Spitfire Audio", "BBC SO Pro €999", "LABS+ £12.99/mo", "LABS (free)", "SINE player", "Expensive; Splice acquisition fears; SINE bugs"),
        ("Native Instruments", "Komplete Ultimate $1,799", "—", "—", "iLok (hated)", "Hardware dongle; insolvency rumors; heavy CPU"),
        ("Output", "—", "Arcade $12.99/mo", "—", "—", "Subscription-only; trust (Splice-owned); mixed quality"),
        ("Heavyocity", "NOVO/Damage $399 ea", "—", "—", "Kontakt", "Niche; expensive; Kontakt dependency"),
        ("Cinesamples", "Musio $299–$399", "Musio $9.99/mo", "—", "Musio player", '"Too good to be true" suspicion; player quality'),
        ("8Dio", "Adagio $499", "—", "—", "Kontakt", "QC issues; Trustpilot 3.1/8; sale fatigue"),
        ("Embertone", "Joshua Bell $199", "—", "—", "Kontakt", "Niche (solo only); small catalog"),
        ("Orchestral Tools", "Berlin Max €1,399", "—", "Berlin Free", "SINE player", "Very expensive; SINE bugs; no Linux"),
        ("EastWest", "—", "ComposerCloud $19.99/mo", "—", "Install centre", "Worst portal software; subscription fatigue"),
    ]
    trad_cells = ""
    for r in trad_rows:
        trad_cells += (
            f"<tr><td class='metric'>{r[0]}</td><td>{r[1]}</td><td class='value'>{r[2]}</td>"
            f"<td>{r[3]}</td><td>{r[4]}</td><td class='muted'>{r[5]}</td></tr>"
        )

    sections.append(f"""
<div class="section">
  <h2 class="section-title">5. Traditional Sample Library Competitors</h2>
  <p><strong>Market:</strong> Orchestral, cinematic, and traditional sample libraries.
    <strong>Size:</strong> ~$1.8B (2025) → $3.9B by 2034 (8.9% CAGR).</p>

  <h3 class="subhead">Incumbent Map</h3>
  <table>
    <thead><tr><th>Competitor</th><th>Premium Anchor</th><th>Subscription</th><th>Freemium Entry</th><th>DRM/Payer</th><th>Core Pain Point</th></tr></thead>
    <tbody>{trad_cells}</tbody>
  </table>

  <h3 class="subhead">Aggregated Industry Pain Points</h3>
  <div class="callout-red">
    <div class="callout-label">Risk / Watch — Industry Pain Points</div>
    <ul style="margin:2pt 0;">
      <li><span class="bullet-dot"></span><strong>DRM &amp; licensing hatred</strong> — iLok hardware
        dongle failures; cloud inconvenient; license transfer restrictions; online verification
        requirements. Universal complaint.</li>
      <li><span class="bullet-dot"></span><strong>Subscription fatigue</strong> — monthly fees stacking
        up; cancel = lose access.</li>
      <li><span class="bullet-dot"></span><strong>Perpetual too expensive</strong> — €799–€1,899 for
        full orchestras; gap between $30 singles and $1,000+ orchestras has no mid-tier option.</li>
      <li><span class="bullet-dot"></span><strong>Storage bloat</strong> — 100GB+ per library; 1TB+
        for full template; 32–64GB RAM recommended.</li>
      <li><span class="bullet-dot"></span><strong>Player instability</strong> — SINE bugs, Kontakt
        crashes, Opus issues; "just works" is an unclaimed position.</li>
      <li><span class="bullet-dot"></span><strong>Splice acquisition anxiety</strong> — Spitfire, Output,
        Sample Magic all under Splice. Users fear forced subscription future; license ownership if
        company goes under.</li>
      <li><span class="bullet-dot"></span><strong>No Linux support</strong> — zero major sample library
        supports Linux. Clear niche.</li>
    </ul>
  </div>

  <h3 class="subhead">Opportunity Gaps — Traditional Libraries</h3>
  <div class="callout-green">
    <div class="callout-label">Opportunity Gaps</div>
    <ul style="margin:2pt 0;">
      <li><span class="bullet-dot"></span><strong>Compressed/AI-assisted libraries</strong> — pro sound
        without 100GB; AI could reduce size 10–50×. No player leadership in this space.</li>
      <li><span class="bullet-dot"></span><strong>Perpetual-friendly subscription hybrid</strong> — "own
        after X payments." Spitfire's Splice rent-to-own is a start; no one offers it for all libraries.</li>
      <li><span class="bullet-dot"></span><strong>Playerless/web-based</strong> — kill iLok + proprietary
        players. Simple license key. Cross-platform (Linux underserved).</li>
      <li><span class="bullet-dot"></span><strong>Transparent mid-tier pricing</strong> — $150–300
        "professional lite" tier is empty. Cinesamples Musio is closest but quality questioned.</li>
      <li><span class="bullet-dot"></span><strong>All-in-one subscription with ownership</strong> —
        subscribe 24 months, own forever. No one offers this.</li>
      <li><span class="bullet-dot"></span><strong>Stability &amp; performance</strong> — "just works"
        positioning could win share.</li>
      <li><span class="bullet-dot"></span><strong>Linux support</strong> — own the zero-coverage niche.</li>
    </ul>
  </div>
</div>
""")

    # ── PAGE BREAK ──
    sections.append('<div class="page-break"></div>')

    # ── 6. PAIN POINTS ──
    sections.append("""
<div class="section">
  <h2 class="section-title">6. Cross-Platform Pain Points — The Sales Playbook</h2>

  <h3 class="subhead">The "Rental" Problem #1</h3>
  <ul>
    <li>Cancel subscription → lose access to downloaded samples (Splice, Loopcloud, Arcade, EastWest)</li>
    <li>Credits expire on cancellation (Splice)</li>
    <li>No perpetual ownership in most subscriptions</li>
  </ul>
  <p style="color:{SIGNAL};"><strong>Sales angle:</strong> "You keep what you download — forever."
    Ownership as a differentiator.</p>

  <h3 class="subhead">Credit/Point System Frustration #2</h3>
  <ul>
    <li>Artificial currency obscures real cost; feels predatory</li>
    <li>Hard to know cost-per-sample; unused credits create anxiety</li>
  </ul>
  <p style="color:{SIGNAL};"><strong>Sales angle:</strong> Transparent pricing. No credits. Know what you pay.</p>

  <h3 class="subhead">Discovery &amp; Quality #3</h3>
  <ul>
    <li>80% of Splice samples criticised as generic; hard to find gems</li>
    <li>Poor metadata/tempo-key tagging on one-shots; genre gaps (world, non-Western, niche)</li>
  </ul>
  <p style="color:{SIGNAL};"><strong>Sales angle:</strong> Curated quality over volume. Better metadata. Genre depth.</p>

  <h3 class="subhead">Technical #4</h3>
  <ul>
    <li>Missing samples when collaborating (Splice); clunky DAW integration (vs Loopcloud seamless)</li>
    <li>Always-on internet for cloud features; resource-heavy desktop apps</li>
  </ul>
  <p style="color:{SIGNAL};"><strong>Sales angle:</strong> Offline-first. DAW-native plugin. No cloud dependency.</p>

  <h3 class="subhead">Pricing Fatigue #5</h3>
  <ul>
    <li>Multiple subscriptions add up ($10–40/mo each); Splice price hikes; hard to justify for hobbyists</li>
    <li>Annual commitments feel risky</li>
  </ul>
  <p style="color:{SIGNAL};"><strong>Sales angle:</strong> One subscription. Flat pricing. No per-user tax.</p>

  <h3 class="subhead">Creator Compensation #6</h3>
  <ul>
    <li>Producers report low per-download payouts on Splice; no royalty transparency</li>
  </ul>
  <p style="color:{SIGNAL};"><strong>Sales angle:</strong> Transparent per-download payouts. Creator profiles. Tip jars.</p>
</div>
""")

    # ── PAGE BREAK ──
    sections.append('<div class="page-break"></div>')

    # ── 7. STRATEGIC POSITIONING ──
    pos_rows = [
        ("Open platform vs. Splice walled garden",
         'Splice owns Spitfire, Output, Sample Magic — your samples live in their ecosystem. '
         'LibreBase is vendor-neutral: your data, your formats, your choice.'),
        ("Perpetual ownership vs. rental",
         "Cancel Splice and you lose 3–4M samples you 'downloaded.' With LibreBase, what you acquire "
         "is yours — no rental, no credit expiry."),
        ("Transparent pricing vs. credit systems",
         "Splice's credit model obscures real cost. LibreBase uses flat, predictable pricing — no "
         "artificial currency, no use-it-or-lose-it."),
        ("AI-native vs. bolt-on AI",
         "Splice Create (April 2026) is AI bolted onto a sample library. LibreBase's open approach "
         "means AI generation + separation + editing + MIDI in one workflow — not a crediting game."),
        ("No DRM vs. iLok / SINE / Kontakt",
         "iLok is universally hated. SINE crashes. Kontakt eats RAM. LibreBase: no dongles, no "
         "proprietary players, no Linux exclusion."),
        ("Mid-market focus vs. enterprise blanks",
         "Sphera and Enablon cost six figures. Consumer subs feel predatory. LibreBase targets the "
         "$150–300 professional-lite gap nobody fills."),
        ("Linux support as wedge",
         "Zero major sample library supports Linux. LibreBase does — own a niche nobody else touches."),
        ("Creator economy vs. black-box royalties",
         "Splice producers report low payouts with no transparency. LibreBase makes attribution and "
         "compensation visible by default."),
    ]
    pos_cells = "\n".join(
        f"<tr><td class='metric'><strong>{p}</strong></td><td class='muted'>{h}</td></tr>"
        for p, h in pos_rows
    )

    sections.append(f"""
<div class="section">
  <h2 class="section-title">7. Strategic Positioning — Where LibreBase Fits</h2>

  <h3 class="subhead">The Open-Knowledge Angle</h3>
  <p>LibreBase's core thesis — <strong>knowledge should be findable, attributable, and freely reusable</strong>
    — maps directly onto every pain point above:</p>
  <ul>
    <li><span class="bullet-dot"></span><strong>No lock-in</strong> — samples, metadata, and workflows
      are yours, portable, exportable. The anti-Splice, anti-iLok, anti-subscription-fatigue platform.</li>
    <li><span class="bullet-dot"></span><strong>Attributable</strong> — every sample, loop, and AI
      generation traced to source. Creator credits visible. Royalty transparency by design.</li>
    <li><span class="bullet-dot"></span><strong>Findable</strong> — open metadata standards (BPM/key/timbre)
      that work across platforms. No walled-garden search.</li>
    <li><span class="bullet-dot"></span><strong>Freely reusable</strong> — perpetual access model. Download
      and own. No credit anxiety. Cancel and keep.</li>
  </ul>

  <h3 class="subhead">Concrete Positions for Sales</h3>
  <table>
    <thead><tr><th style="width:35%;">Position</th><th>Sales Hook</th></tr></thead>
    <tbody>{pos_cells}</tbody>
  </table>

  <h3 class="subhead">Competitors to Watch</h3>
  <ul>
    <li><span class="bullet-dot"></span><strong>BandLab</strong> — dark horse. Free tier (20 samples/mo +
      social distribution) pulling Gen Z. Watch for bundling momentum.</li>
    <li><span class="bullet-dot"></span><strong>Splice consolidation</strong> — Spitfire + Output +
      Sample Magic under one roof. User trust erosion is real; opportunity for vendor-neutral alternative.</li>
    <li><span class="bullet-dot"></span><strong>Text-to-sample generators</strong> — ILLUGEN, Text-to-Sample,
      Splice Create, Loudly. Fragmented, quality varies, no DAW-native leader. First mover here wins.</li>
    <li><span class="bullet-dot"></span><strong>Magenta/Google</strong> — free, open weights, real-time
      synthesis. If Google productises, it undercuts paid tools. LibreBase's open-data angle is parallel
      and complementary.</li>
  </ul>
</div>
""")

    # ── PAGE BREAK ──
    sections.append('<div class="page-break"></div>')

    # ── 8. QUICK-REFERENCE CARD ──
    obj_rows = [
        ("'Splice has the biggest library'",
         "Yes — 3–4M+ samples, 22% share. But 80% of users call them generic, credits expire, and "
         "cancel means losing everything. We offer ownership + curation, not volume + rental."),
        ("'Loopcloud integrates with my DAW'",
         "Loopcloud's plugin is strong, but it's cloud-dependent and points-based. We're DAW-native, "
         "offline-capable, and flat-priced — no credit maths."),
        ("'I've already paid for Kontakt libraries'",
         "Kontakt's iLok DRM is the #1 complaint in the industry. We're playerless — no dongles, no "
         "proprietary lock-in. Your existing libraries stay yours."),
        ("'AI sample gen is gimmicky'",
         "Waves ILLUGEN scored 5/10 from MusicTech. Splice Create is new and unproven. But Samplab's "
         "shutdown (Sept 2026) left a real gap — the market wants generation + editing in one tool. "
         "We're building toward that."),
        ("'Enterprise tools are more trustworthy'",
         "Sphera and Enablon cost $16K–$100K+ and are overkill for anyone under $500M revenue. "
         "Mid-market is underserved. We're built for teams that need AI-powered review without the "
         "enterprise tax."),
    ]
    obj_cells = "\n".join(
        f"<tr><td class='metric'><strong>{o}</strong></td><td class='muted'>{r}</td></tr>"
        for o, r in obj_rows
    )

    nums = [
        ("$1.8B", "Current sample library market (2025)"),
        ("8.9–9.5% CAGR", "Sustained growth through 2034"),
        ("22%", "Splice market share (leader, not monopoly)"),
        ("6M+", "Splice registered users (churn opportunity)"),
        ("$34.99/mo", "Splice Sounds 1000 (price hike flashpoint)"),
        ("Trustpilot scores", "Splice 4.3 / Output 3.7 / EastWest 3.4 / 8Dio 3.1 / Heavyocity 2.5 / Tracklib 2.0 / Noiiz 2.2"),
        ("Samplab shutdown", "Sept 17, 2026 — leaves polyphonic note-editing gap"),
    ]
    num_cells = "\n".join(
        f"<tr><td class='value'><strong>{n}</strong></td><td class='muted'>{c}</td></tr>"
        for n, c in nums
    )

    signal_bullets = [
        "Splice price trajectory post-Spitfire/Output acquisitions — user churn sentiment",
        "BandLab's free-tier growth — Gen Z creator pull",
        "Any Google productisation of Magenta RealTime 2 — free AI undercutting paid tools",
        "Text-to-sample quality improvements — when does it become production-ready?",
        "Linux adoption in music production — growing but still zero competitor support",
    ]
    sig_html = "\n".join(
        f"<li><span class='bullet-dot'></span>{s}</li>" for s in signal_bullets
    )

    sections.append(f"""
<div class="section">
  <h2 class="section-title">8. Quick-Reference Card — Sales Ready</h2>

  <h3 class="subhead">Top 5 Objections &amp; Responses</h3>
  <table>
    <thead><tr><th style="width:30%;">Objection</th><th>Response</th></tr></thead>
    <tbody>{obj_cells}</tbody>
  </table>

  <h3 class="subhead">Key Numbers to Quote</h3>
  <table>
    <thead><tr><th style="width:25%;">Metric</th><th>Value / Context</th></tr></thead>
    <tbody>{num_cells}</tbody>
  </table>

  <h3 class="subhead">Signals to Monitor</h3>
  <ul>{sig_html}</ul>
</div>

<div class="sources">
  Sources: Market Intelo, Dataintelo, Trustpilot, Reddit (r/edmproduction, r/makinghiphop,
  r/spitfireaudio, r/composer, r/musicproduction), Music Business Worldwide, Output Inc comparison
  guides, Splice / Loopcloud / Tracklib / Spitfire / NI / Output / Heavyocity / Cinesamples /
  8Dio / Embertone / Orchestral Tools / EastWest official pricing pages, Vi-Control forums, KVR Audio,
  Gearspace, Attack Magazine, BandLab Help Center, MusicRadar, MusicTech reviews, Adobe Podcast,
  Google Magenta project docs, Samplab / RipX / Waves / Text-to-Sample / Loudly official pages.
  Research consolidated August 16–18, 2026. All pricing and metrics as of date of research.
</div>
""")

    # ── ASSEMBLE ──
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>LibreBase Market Research Brief</title>
<style>{brand_css()}</style>
</head>
<body>
<div class="page">
{"".join(sections)}
</div>
</body>
</html>"""
    return html


def render_pdf(html_content, output_path):
    """Use Chromium headless to print HTML → PDF."""
    # Write HTML to a temp file
    tmp = tempfile.mkdtemp(prefix="librebase-pdf-")
    html_path = os.path.join(tmp, "brief.html")
    with open(html_path, "w") as f:
        f.write(html_content)

    args = [
        CHROME,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--print-to-pdf=" + output_path,
        "--print-to-pdf-no-header",
        "--window-size=595,842",   # A4 at 96dpi
        "--margin-top=20mm",
        "--margin-bottom=22mm",
        "--margin-left=18mm",
        "--margin-right=18mm",
        html_path,
    ]
    print(f"  Running Chromium headless (this may take a moment)...")
    result = subprocess.run(args, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        print(f"  STDOUT: {result.stdout}")
        print(f"  STDERR: {result.stderr}")
        # Fallback: try without --window-size
        args2 = [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
                 "--print-to-pdf=" + output_path, html_path]
        result2 = subprocess.run(args2, capture_output=True, text=True, timeout=120)
        if result2.returncode != 0:
            print(f"  FALLBACK STDERR: {result2.stderr}")
            return False
    # Cleanup
    shutil.rmtree(tmp, ignore_errors=True)
    return True


def main():
    html = build_html()
    tmp_html = os.path.join(os.path.dirname(OUTPUT_PATH), "_tmp_brief.html")
    with open(tmp_html, "w") as f:
        f.write(html)
    print(f"  HTML written: {len(html):,} chars -> {tmp_html}")

    if not render_pdf(html, OUTPUT_PATH):
        print("  ERROR: Chromium PDF failed")
        sys.exit(1)

    size = os.path.getsize(OUTPUT_PATH)
    print(f"  ✓ PDF written: {OUTPUT_PATH}")
    print(f"  Size: {size:,} bytes")
    return True


if __name__ == "__main__":
    main()
