# Librebase socials video — HyperFrames composition

Branded 9:16 (1080×1920) social cut of the vision story: **Supabase's vision —
without the cost, without the wait.** Built as a HyperFrames HTML composition
(see `docs/demo/librebase-vision-video-script.md` for the full story).

## Composition spec

| Property | Value |
| --- | --- |
| Resolution | 1080×1920 (9:16) |
| Duration | 26 s |
| FPS | 30 |
| Scenes | Hook → Footprint → Provisioning → Compat → Outro |
| Brand | Librebase tokens (`#0a0a0a` bg, `#495d36` accent, IBM Plex Sans) |

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
npx hyperframes snapshot . --at 2.0,7.5,13.0,18.0,23.5 --output renders
```

## Motion design

Composed from the HyperFrames `motion-graphics` + `hyperframes-animation` skill
set (atomic rules: `spring-pop-entrance`, `counting-dynamic-scale`,
`stat-bars-and-fills`, `kinetic-beat-slam`, `logo-assemble-lockup` blueprint).
One paused GSAP timeline registered on `window.__timelines["librebase-socials"]`;
deterministic, no render-time clocks.

## Copy

- **Hook:** Supabase's vision — "Compatible. *Not* Supabase-sized."
- **Footprint:** 8 MB image vs ~7.5 GB full stack / 12 containers.
- **Provisioning:** 265 ms cold start → healthy.
- **Compat:** 111/111 core Data API on the official postgrest-js suite.
- **Outro:** librebase.xyz + honest footnote (Realtime & Storage still catching up).
