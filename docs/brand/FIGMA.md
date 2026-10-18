# Figma → Librebase brand sync

The **blue bird** identity lives in Figma. Agents and CI should treat that file as the source of truth for logo SVGs and color tokens—not the legacy Majico sage-green export in `majico-export/`.

## Figma MCP (this environment)

- Connected account: **Julian Kleber** (`julian.kleber@obsevia.com`), Pro team `team::1577975305834753111`.
- MCP can **create** files (verified). It cannot **read** the brand file until that file is shared with this account with at least **can view** (Figma MCP currently returns *"don't have edit access"* for unknown or restricted keys).

## What we need from you

1. Open the brand file in Figma (blue palette + bird mark).
2. **Share** it with `julian.kleber@obsevia.com` (viewer is enough if MCP allows read; editor if tools require it).
3. Paste the design URL in chat, e.g.  
   `https://www.figma.com/design/<FILE_KEY>/Librebase-Brand?node-id=...`

## Agent workflow (once URL is known)

1. `create_session` with `fileKey` from the URL.
2. `get_metadata` (no `nodeId`) → list pages; pick **Logo** / **Brand** / **Tokens**.
3. `get_variable_defs` or `get_design_context` on logo + primary color styles.
4. `download_assets` on the bird mark node → save under `data-studio-ui/public/brand/`.
5. Update tokens per [STUDIO.md](./STUDIO.md):
   - `data-studio-ui/app/globals.css` (`--accent`, `--lb-signal`, landing `--lb-*`)
   - `docs/brand/DESIGN.md`, `docs/brand/BRAND.md`
6. Wire logo in nav (`lb-wordmark` / `StudioFrame` header) and `app/icon` + `og.png` if provided in Figma.

## Repo state before sync

- Studio + landing still use **teal/sage** tokens (`#1f7a6e`, `#2fd4c2`) from the 2026 Majico handoff.
- `BRAND.md` still says no official logo in repo scope—that should be revised after Figma assets land.

## Temporary test file (safe to delete)

A blank file was created only to verify MCP write access:  
https://www.figma.com/design/F3IKCFzFN9fU74eek1hXWf (`Librebase Brand Sync Test`)
