# Librebase socials video — HyperFrames composition

Branded 9:16 (1080×1920) social cut of the vision story: **sub-second
provisioning, sandbox-sized footprint, prototype→production path.** Built as a
HyperFrames HTML composition (see `docs/demo/librebase-vision-video-script.md`
for the full story).

## Composition spec

| Property | Value |
| --- | --- |
| Resolution | 1080×1920 (9:16) |
| Duration | 26 s |
| FPS | 30 |
| Scenes | Hook → Footprint → Provisioning → Compat → Outro |
| Brand | Librebase landing design system (`#0a0a0a` bg, `#ff7800` accent, gradient-text wordmark, system-ui) |

## Preview locally

Open `index.html` directly in a browser, or run the Studio:

```bash
npx hyperframes preview .
```

## Render MP4 (requires Node ≥22 + FFmpeg)

```bash
npx hyperframes render . -o renders/librebase-socials.mp4
```

## Snapshot frames

```bash
npx hyperframes snapshot . --at 2.2,7.2,13.5,18.5,24.5 --output renders
```

## Motion design

Composed from the HyperFrames `motion-graphics` + `hyperframes-animation` skill
set (atomic rules: `spring-pop-entrance`, `counting-dynamic-scale`,
`stat-bars-and-fills`, `kinetic-beat-slam`, `logo-assemble-lockup` blueprint).
One paused GSAP timeline registered on `window.__timelines["librebase-socials"]`;
deterministic, no render-time clocks.

## Copy

- **Hook:** The vision — "Sub-second. Sandbox-sized."
- **Footprint:** 8 MB image / 1 container; ~2 MB idle vs ~1.85 GB hosted / ~140 MB containerized.
- **Provisioning:** 265 ms cold start → healthy. "Give one to every prototype."
- **Compat:** 111/111 Core Data API on the official PostgREST client suite, as-is no shims.
- **Outro:** "Sandbox footprint. Production path." + librebase.xyz + honest footnote (Realtime & Storage still catching up).
