---
name: majico-brand-handoff
description: Apply Majico brand to code — read BRAND.md + DESIGN.md, map tokens, match voice. Flexible guide, not a rigid checklist.
---

# Majico brand handoff

Use when applying a Majico brand to a consumer repo (portal, app, marketing site).

## Read first (in order)

1. **BRAND.md** — voice, positioning, do's/don'ts
2. **DESIGN.md** — tokens, typography, components, layout
3. Project UI conventions — match the stack already in the repo

Fetch via Majico MCP when connected: `get_brand_md`, `get_design_md`, `get_design_tokens`, `get_logo_svg`.

## Apply brand (adapt to the codebase)

- Map design tokens to CSS variables, Tailwind theme, or your existing token layer — avoid hardcoding brand hex in components.
- Use heading/body font pairing from DESIGN.md; load fonts the way the project already loads fonts.
- Reserve accent color for CTAs, links, and emphasis — not decorative fills everywhere.
- Hero pattern when building marketing: **headline → subcopy → CTA** (flex order if the product already established a different pattern; explain why).
- Full marketing pages: load **`landing-page-oneshot`** for section order, hero budget, CTA strategy, proof, and verification.

## Voice

- Write copy from BRAND.md tone; prefer outcome-first sentences.
- Skip consultant jargon and generic "AI-powered" lead copy unless the brand explicitly uses it.
- Apply anti-slop: no em dashes, no `; and`, no stock antithesis.

## When stuck

- Prefer the brand docs over generic UI templates.
- If MCP returns empty brand data, ask the user to finish the Majico canvas flow first.
- Finish Studio handoffs with `ack_cursor_handoff` when applicable.
