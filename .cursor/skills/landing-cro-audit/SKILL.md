---
name: landing-cro-audit
description: CRO audit for marketing landings - conversion goal, CTA consistency, friction, proof placement, form UX, section order vs landing-page-oneshot. Use when auditing, reviewing, or fixing conversion on a waitlist/signup/demo landing.
phase: verify
priority: 23
is_system: true
---

# Landing CRO audit

Use after building or when the user asks to audit conversion on a marketing landing (waitlist, trial, book-a-demo).

Pair with **`landing-page-oneshot`** (build playbook). This skill is the conversion scorecard and fix loop.

## Load order

1. `sync_cursor_skills` if skills are not local
2. `landing-page-oneshot` (section order, hero budget, anti-slop)
3. This skill (`landing-cro-audit`)
4. `ui-ship-check` before claiming done

## Primary conversion goal (mandatory)

State the single primary goal in one line before changing copy:

- Example: `Waitlist email submit for early access`
- Example: `Book a demo`

Every primary button, nav CTA, mid-page CTA, and final CTA must use the **same label** and same destination. Secondary CTAs stay quieter (docs, Studio, pricing jump).

## Audit checklist (score each Pass / Fail / N/A)

### Goal and CTAs

- [ ] One primary conversion goal for the whole page
- [ ] Identical primary CTA label in nav, hero, optional mid-page, form submit, and final band
- [ ] Primary CTA names the action (Join the waitlist for early access, Start free trial, Book a demo). Not Learn more.
- [ ] Secondary CTA does not compete visually with primary

### Friction

- [ ] Form asks only for fields needed for the goal (email alone is fine for waitlist)
- [ ] Submit button restates the goal (not Submit / Send)
- [ ] Success and error states are clear and on-page
- [ ] No guilt copy (No spam, We hate spam) unless brand docs require it. Prefer outcome reassurance if any.

### Proof and trust

- [ ] Proof bar under hero uses real claims only (omit logos/metrics you cannot verify)
- [ ] Honest status is OK (capability matrix, incomplete rows). Fake social proof is Fail.
- [ ] Trust sits near the signup moment (security note, self-host option, Studio open today)

### Structure (vs oneshot)

- [ ] Scroll order: nav → hero → proof → problem → how → benefits → (optional mid CTA) → FAQ objections → final CTA → footer
- [ ] Pricing skipped only when the offer is waitlist/invite (document the skip)
- [ ] Deep testimonials skipped when none exist (do not invent)
- [ ] FAQ covers top objections before or beside the final ask (parity, self-host, security, pricing model)

### Attention and copy

- [ ] Hero budget respected (brand, one H1, one support line, one CTA group, one visual)
- [ ] One job per section
- [ ] Anti-slop: no em/en dashes, no stock antithesis, concrete verbs
- [ ] Mobile: primary CTA thumb-reachable, form usable without zoom

## Fix loop

1. Write Pass/Fail table for the checklist (cite section ids or selectors).
2. Fix Fail items in priority order: CTA consistency → form submit label → section order → anti-slop → proof honesty.
3. Re-run this checklist. Stop when all applicable rows are Pass.
4. For Majico Studio handoffs, call `ack_cursor_handoff` when applicable.

## Handoff note for agents

When `get_cursor_handoff` / `sync_cursor_skills` runs for landing work, load **`landing-page-oneshot`** to build and **`landing-cro-audit`** before shipping or when the user asks for a CRO pass.

## Related

- `landing-page-oneshot` - build playbook
- `ui-ship-check` - completion gate
- `majico-brand-handoff` - brand apply
