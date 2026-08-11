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

- **Hook:** Meet Librebase — "Tiny backend as a service." / "Small enough to spin up for every idea."
- **Footprint:** Idle memory (hosted ~1.85 GB / Postgres+GoTrue+PostgREST ~140 MB / Librebase ~2 MB). Pill: "All built in one tiny container image."
- **Cold start:** 265 ms → ready. "Up before you finish the thought."
- **Value:** Prototype. Ship. Stay lean.
- **Outro:** Wordmark + "Lean backend for apps and AI tools." + librebase.xyz

Numbers from `benchmarks/full-stack/results/footprint-provisioning.json` (RSS idle).
