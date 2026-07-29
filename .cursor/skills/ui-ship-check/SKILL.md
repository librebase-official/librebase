---
name: ui-ship-check
description: Light verification before claiming UI work done — tests and themes, not bureaucracy.
---

# UI ship check

Use before saying UI work is complete.

## Quick pass

- Light and dark themes if the product supports both
- Tokens used instead of stray hardcoded brand colors
- Primary flows still work (navigation, forms, main CTA)
- Copy still matches BRAND.md voice at a glance
- Marketing landings: run the **`landing-page-oneshot`** verification checklist (hero budget, section order, CTA consistency, anti-slop)

## Tests (match project norms)

- UI/CSS fixes: add or update a test the project would actually run (component test or CSS regression if that's the pattern).
- Don't add throwaway tests that only assert static strings.

## Optional

- **verification-before-completion** plugin skill if installed
- Visual check in browser for the viewport sizes this product cares about

## Done means

- You can describe what changed and why it matches brand + UX intent
- Known gaps are called out honestly — not hidden
