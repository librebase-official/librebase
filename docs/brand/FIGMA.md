# Figma → Librebase brand sync

**Source file:** [li — librebase final](https://www.figma.com/design/YGRFmItfhPVBdpPsYmWyQZ/li?node-id=327-8199) (`fileKey` `YGRFmItfhPVBdpPsYmWyQZ`)

## Palette (from Figma “Color Palette” frame)

| Token | Hex | Use |
| --- | --- | --- |
| Twitter Blue (primary) | `#008FF0` | Accent, CTAs, icon background |
| White | `#FDFDFD` | Text on blue, paper |
| Deep Blue | `#051114` | Marketing ink / dark bg |
| Slate Grey | `#052A43` | Panels, dark surfaces |
| Grey Blue | `#E2F1FB` | Soft fills, secondary text (light mode) |

## Exported assets (repo)

| File | Figma node |
| --- | --- |
| `data-studio-ui/public/brand/librebase-mark.svg` | Icon pattern `417:1681` (bird on blue) |
| `data-studio-ui/public/brand/librebase-logo-full.svg` | Full lockup `423:22326` |
| `data-studio-ui/public/brand/librebase-logo-lockup.png` | Compact lockup `522:22394` |
| `data-studio-ui/public/og.png` | Icon export (PNG) |
| `data-studio-ui/app/icon.png` | App icon |

Studio uses `IconMark` → `/brand/librebase-mark.svg`. CSS tokens: `data-studio-ui/app/globals.css` (`--accent`, `--lb-signal`, marketing `--lb-*`).

## Re-sync after Figma changes

1. `create_session` with `fileKey` `YGRFmItfhPVBdpPsYmWyQZ`.
2. `download_assets` on `417:1681` (icon) and `423:22326` (full logo).
3. Refresh `librebase-mark.svg` if the bird vectors changed; update `:root` / `[data-theme="dark"]` if palette text in frame `522:22356` changes.
