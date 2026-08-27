# Librebase vs open stack — HyperFrames composition

Branded 9:16 (1080×1920) social cut. Matches the live landing design system
(`data-studio-ui`): Orbitron wordmark, Space Grotesk body, teal signal accent.

## Composition spec

| Property | Value |
| --- | --- |
| Resolution | 1080×1920 (9:16) |
| Duration | 28 s |
| FPS | 30 |
| Scenes | Hook → Footprint → Vector QPS → Speed board → Outro |
| Brand | Landing tokens (`#071014` ink, `#2fd4c2` signal, Orbitron + Space Grotesk) |
| Competitor label | **open stack** |

## Preview

```bash
npx hyperframes preview .
```

## Render MP4 (Node ≥22 + FFmpeg)

```bash
npx hyperframes render . -q high -o ../renders/librebase-benchmark.mp4
```

## Snapshot frames

```bash
npx hyperframes snapshot . --at 2.0,8.0,14.0,20.0,25.5 --output ../renders
```

## Copy

- **Hook:** Librebase vs open stack — same machine, same tests, honest numbers.
- **Footprint:** Open stack ~1.85 GB / 12 containers vs Librebase ~2 MB / 1 container; cold start 265 ms.
- **Vector:** 4,683 QPS @ 100% recall — 9.4× the open stack at equal accuracy.
- **Board:** Auth, storage, ingest, lookup — Librebase wins each row.
- **Outro:** Start now · librebase.xyz · Measured, not marketed.

Numbers from `benchmarks/full-stack/results/vector-fresh-2026-08-13.json` and full-palette results.
