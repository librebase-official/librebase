---
name: ui-craft-polish
description: Craft components, motion, and micro-interactions — polish UX without over-engineering.
---

# UI craft and polish

Use while implementing UI after tokens and layout direction exist.

## Components

- Reuse existing components and patterns in the repo before adding new abstractions.
- States matter: default, hover, focus-visible, disabled, loading, empty, error — implement what the surface actually needs.
- Spacing: prefer the project's scale (or Majico `--size-*` / token spacing if the repo adopted them).

## Motion (when it helps)

- Prefer transform + opacity; respect `prefers-reduced-motion`.
- Stagger entrances lightly (roughly 80–120ms) — skip motion if it adds noise.
- If Figma MCP is connected, **figma-implement-motion** can translate specs — optional.

## Accessibility

- Contrast for text on tinted backgrounds; don't rely on color alone for state.
- Labels for icon buttons; sensible heading order.

## Figma parity (optional)

With Figma MCP: load **figma-use** first, then **figma-generate-design** or **figma-generate-library** if the user wants design-file parity — not required for every task.

## Anti-patterns

- Don't add design-system layers the repo doesn't need.
- Don't chase pixel-perfect clones of reference sites when brand tokens should drive the look.
