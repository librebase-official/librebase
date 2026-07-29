---
name: landing-page-oneshot
description: One-shot on-brand SaaS/product landing page playbook - section order, hero budget, CTAs, proof, SEO basics, motion budget, verification. Load before building or publishing marketing landings.
---

# Landing page oneshot

Use when building, rewriting, or publishing a marketing landing page in a consumer repo or via Majico `publish_landing_page` / harness `landing-page`.

Goal: ship a complete, on-brand page in one pass. Do not invent a second design system when BRAND.md, DESIGN.md, and tokens already exist.

## Load order (required)

1. `sync_cursor_skills` / `get_ui_ux_skills` if skills are not local
2. `majico-brand-handoff` (or `majico-branding-sync`) then `get_brand_md`, `get_design_md`, `get_design_tokens`, `get_logo_svg`
3. This skill (`landing-page-oneshot`)
4. Optional: `ui-layout-discover` for IA sketch, `ui-motion-expressive` only after asking about motion intensity, `ui-ship-check` before claiming done
5. Studio canvas HTML: also follow harness skill `landing-page` (research + htmlFrame bundle)

Brand docs win over generic SaaS templates. Map colors, type, and spacing from DESIGN.md / tokens. Never hardcode brand hex in components.

## Required section checklist (ordered)

Build in this scroll order unless the brief explicitly drops a section (note the skip in your plan):

1. **Nav** - logo (brand-level), primary CTA, optional secondary link. Keep chrome light.
2. **Hero** - see hero budget below. One composition. Brand as a hero-level signal.
3. **Proof bar** - logos, user count, or review badge immediately under the hero (cold traffic needs trust before feature depth).
4. **Problem / promise** - one job: name the pain and the outcome. Short.
5. **How it works** - 3 steps max, or a short product demo / real UI visual.
6. **Benefits or features** - 3 to 5 outcomes with product proof (screenshot, workflow, or concrete mechanism). Benefit headline first.
7. **Deep social proof** - testimonials with role + company, or a measurable result. Place near hesitation points (after claims, before/after pricing).
8. **Pricing** - clear tiers or a single offer. Highlight one recommended path. Match brief CTAs (trial vs book-a-call).
9. **FAQ** - 5 to 8 objections (security, migration, pricing, support, cancel). Accordion is fine on mobile.
10. **Final CTA** - restate the core outcome + the same primary CTA as the hero.
11. **Footer** - legal, product links, contact. No new competing offers.

One job per section: one headline, one short supporting line, then content. Cut dashboard clutter, stat strips, and promo chips that steal focus from the section job.

## Hero budget / first viewport

The first viewport is one composition, not a mini-dashboard.

Allowed:

- Brand or product name at hero-level prominence (logo + wordmark or title treatment from brand docs)
- One outcome headline (specific, scannable, roughly under 10 words when possible)
- One short supporting sentence (audience + mechanism)
- One CTA group (primary required, secondary optional)
- One dominant visual: full-bleed product shot, atmospheric brand visual, or approved hero asset

Forbidden in the hero:

- Stat grids, schedule snippets, address blocks, multi-card feature grids
- Detached floating badges, promo stickers, or callout chips on top of hero media
- Inset / side-panel / tiled collage heroes on promotional landings (prefer full-bleed)
- Cards used only for decoration (cards only when interaction needs a container)
- Default stacks (Inter, Roboto, Arial, system) when DESIGN.md specifies brand fonts

Primary CTA label must name the action (`Start free trial`, `Book a demo`, `Start brand flow`). Avoid vague `Learn more` as the only CTA.

Optional micro-reassurance under the CTA: `No credit card`, `Setup in minutes`, or brand-approved trust line.

## CTA strategy

- One primary conversion goal for the whole page. Repeat that same primary CTA in nav, hero, mid-page (optional), and final CTA.
- Secondary CTA is optional and quieter (demo, pricing jump, docs). Never equal visual weight to primary.
- Match positioning: agency/services briefs use book/strategy CTAs. SaaS briefs use trial/signup when the brief says so.
- Place trust next to money or signup moments (logo strip, security note, short testimonial).

## Social proof / trust

- Prefer specific proof (`Trusted by engineering teams at…`, named roles, measurable results) over empty `Trusted by thousands`.
- Early proof bar after hero. Deep proof before pricing or beside the final CTA.
- Do not invent logos, quotes, or metrics. Use brand context, canvas assets, or ask the user.

## On-brand constraints

- Voice, vocabulary, and do/don't from BRAND.md
- Tokens, type scale, components, layout, and DESIGN.md §7 motion from design docs
- Logo variants from `get_logo_svg` / export. Prefer filled vs outline as brand docs specify.
- Theme follows the project (light or dark). Do not force a purple gradient or cream-serif default look when the brand specifies otherwise.

## Copy anti-slop (hard)

Apply Majico anti-slop on every string you write:

- No em dashes or en dashes. Prefer commas, periods, colons, or parentheses.
- No `; and` constructions.
- No stock antithesis (`X, not Y`, `It's not X, it's Y`). State the positive claim.
- Prefer concrete verbs. Skip filler: delve, landscape, robust, seamless, leverage, unlock, elevate (unless BRAND.md uses them on purpose).

## SEO basics (no stuffing)

- One clear H1 that matches the hero promise
- Title and meta description that name the outcome + audience (unique per page)
- Descriptive alt text on the hero and key product images
- Logical heading order (H2 per section). Internal links to pricing/FAQ when useful.
- Canonical, OG image, and sitemap belong to the host app. Do not keyword-stuff body copy.

Pair with harness `seo-foundations` or `majico-blog-seo-handoff` when the user asks for a full SEO pass.

## Motion budget

Default: static is fine. Ask before adding motion (`ui-motion-expressive`).

When motion is wanted, ship **2 to 3 intentional motions** that create hierarchy:

1. Hero entrance (opacity + transform on headline or visual)
2. One scroll reveal for a key proof or product band
3. Optional CTA or focus feedback

Rules:

- Use DESIGN.md §7 / token durations and easing. Transform + opacity only for continuous motion.
- Honor `prefers-reduced-motion: reduce` (instant final state, no infinite pulses).
- Motion is hierarchy, not noise. No ambient particle fields or endless carousels unless the brief requires them.

## Anti-patterns

| Avoid | Do instead |
| --- | --- |
| Feature dump in the hero | Outcome headline + one visual + one CTA group |
| Generic Inter/purple SaaS skin | Brand fonts + tokens from DESIGN.md |
| Decorative card grids | Flat sections. Cards only for real interaction |
| Multiple primary CTAs with different goals | One primary goal, repeated |
| Fake testimonials or metrics | Real brand proof or omit the claim |
| Em dashes and antithesis copy | Short direct sentences (anti-slop) |
| Motion everywhere | 2 to 3 intentional beats max |

## Verification checklist (before done)

- [ ] Section order matches the checklist (or skips are documented)
- [ ] Hero budget respected (brand, one headline, one support line, one CTA group, one dominant visual)
- [ ] Primary CTA consistent across nav / hero / final CTA
- [ ] Colors, type, and logo from brand docs / tokens (no stray brand hex)
- [ ] Proof is real or omitted. FAQ covers top objections when pricing or signup exists.
- [ ] Copy passes anti-slop scan
- [ ] Motion budget ok + reduced-motion path
- [ ] Mobile: CTA thumb-reachable, hero readable without horizontal scroll
- [ ] `ui-ship-check` (and project tests) run. For Studio handoffs, `ack_cursor_handoff` when applicable.

## Related skills

- `majico-brand-handoff` - brand apply
- `ui-layout-discover` - section rhythm before large diffs
- `ui-motion-expressive` - tokenized motion after user opts in
- `ui-craft-polish` - component polish
- `ui-ship-check` - completion gate
- Harness `landing-page` - canvas htmlFrame generation with research
