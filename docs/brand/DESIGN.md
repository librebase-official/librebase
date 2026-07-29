# Librebase DESIGN.md

Interim design system for marketing + Studio continuity until Majico export ZIP lands (`hasBrandData`).

## Color

| Token | Value | Use |
|-------|-------|-----|
| `--lb-ink` | `#071014` | Page ground |
| `--lb-panel` | `#0E1A1C` | Surfaces |
| `--lb-fog` | `#9BB0AA` | Muted text |
| `--lb-paper` | `#E7F2EC` | Primary text on ink |
| `--lb-signal` | `#2FD4C2` | Accent, CTA, brand mark |
| `--lb-signal-dim` | `#1FA89A` | CTA hover |
| `--lb-warn` | `#E8A838` | Honest degraded / caution |
| `--lb-line` | `rgba(231, 242, 236, 0.12)` | Rules |

## Typography

- Display: **Syne** (expressive, geometric). Hero brand + H1.
- Body: **Figtree** (readable, not Inter/Roboto/Arial/system).
- Mono: **IBM Plex Mono** for SQL / status snippets.

## Layout

- Marketing: full-bleed hero, brand-first, one CTA group, one dominant product visual.
- Studio: keep shell density. Map accent to `--lb-signal` when theming.

## Motion (§7)

Durations: enter `480ms`, reveal `560ms`, ease `cubic-bezier(0.22, 1, 0.36, 1)`.
Ship exactly three motions on the landing: hero brand settle, hero visual drift, scroll reveal on promise band.
Honor `prefers-reduced-motion: reduce`.

## Components

- Primary button: filled signal on ink text.
- Secondary: ghost line + paper text.
- No decorative cards in the hero.
