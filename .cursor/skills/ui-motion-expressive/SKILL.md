---
name: ui-motion-expressive
description: Apply per-brand expressive motion from DESIGN.md §7 — ask user about intensity, recommend Motion One for React repos, always respect prefers-reduced-motion.
---

# UI motion (expressive)

Use when the user wants motion in a consumer repo after Majico brand handoff.

## Before animating — ask the user

1. **Do they want motion at all?** Never add motion by default without discussing it.
2. **Intensity:** Reduced (minimal UI transitions), Standard (marketing + app chrome defaults), or Cinematic (longer choreography for hero/marketing beats).
3. **Stack:** React/Next → recommend **Motion One** (`motion` package). CSS-only transitions are always valid — never force dependencies.

Fetch per-brand values via Majico MCP: `get_design_md` (§7 Elevation and Motion), `get_design_tokens`.

## Token names to use

Read durations and easing from DESIGN.md §7 / `design_tokens_json.motion` — do not guess literals:

- `durationMicro`, `durationFast`, `durationNormal`, `durationEmphasis`, `durationChoreography`
- `easingStandard`, `easingExpressive`
- `staggerSibling`, `staggerStream`, `holdReadable`

Map to CSS vars (`--ds-motion-*`) or Motion One `transition` / `animate` props using the same names.

## Implementation rules

- Animate **transform + opacity** only for continuous motion (no width/height/layout thrash).
- Entrances: prefer `easingExpressive` on hero/FLIP; `easingStandard` on UI chrome.
- Stagger siblings ~80–120ms; stream cadence per `staggerStream` when applicable.
- One focal element per beat on marketing surfaces.

## prefers-reduced-motion checklist

- [ ] `prefers-reduced-motion: reduce` → instant final state (no stagger, no long choreography)
- [ ] No autoplay loops that cannot be paused when reduced motion is on
- [ ] Focus rings and state changes remain visible without motion

## Libraries (opt-in)

| Stack                      | Recommendation                                           |
| -------------------------- | -------------------------------------------------------- |
| React / Next.js            | Motion One (`motion`) — declarative, compositor-friendly |
| Static HTML / reel capture | CSS transitions + FLIP; match token easings              |
| No new deps                | CSS-only using `--ds-motion-*` vars from DESIGN.md       |

Pair with Majico `ui-craft-polish` and external `fixing-motion-performance` when polishing.

On marketing landings, follow **`landing-page-oneshot`** motion budget: 2 to 3 intentional hierarchy beats, not ambient noise.

## Anti-patterns

- Do not cap expressive hero choreography to 200ms “for performance” when the brand tier is Cinematic.
- Do not add Framer Motion unless the user explicitly requests it — Motion One is the Majico default for React.
