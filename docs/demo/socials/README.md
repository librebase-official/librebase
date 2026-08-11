# Librebase socials video — HyperFrames composition

Branded 9:16 (1080×1920) social cut. Matches the live landing design system
(`data-studio-ui`): Orbitron wordmark, Space Grotesk body, teal signal accent.

## Composition spec

| Property | Value |
| --- | --- |
| Resolution | 1080×1920 (9:16) |
| Duration | 24 s |
| FPS | 30 |
| Scenes | Hook → Footprint → Cold start → Path → Outro |
| Brand | Landing tokens (`#071014` ink, `#2fd4c2` signal, Orbitron + Space Grotesk) |
| Wordmark | `Libre` + teal `base` (same as `lb-wordmark`) |

## Preview locally

```bash
npx hyperframes preview .
```

## Render MP4 (requires Node ≥22 + FFmpeg)

```bash
npx hyperframes render . -q high -o renders/librebase-socials.mp4
```

## Snapshot frames

```bash
npx hyperframes snapshot . --at 2.0,7.0,12.5,17.5,22.0 --output renders
```

## Copy

- **Hook:** Meet Librebase — "Small enough to spin up for every idea."
- **Footprint:** Idle memory bars (hosted / container / Librebase ~2 MB).
- **Cold start:** 265 ms → ready. "Up before you finish the thought."
- **Path:** Prototype. Ship. Same stack.
- **Outro:** Wordmark + "PostgreSQL for apps and AI tools." + librebase.xyz
