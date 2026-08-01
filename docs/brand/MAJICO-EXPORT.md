# Majico export note

Downloaded 2026-07-30 / refreshed 2026-08-01 (staging five-PDF export).

| Artifact | Path |
|----------|------|
| Export ZIP | `docs/brand/librebase-brand-export.zip` |
| Export ZIP contents | `docs/brand/majico-export/` |
| **Share pack (PDFs)** | `docs/brand/pdfs/` |
| ICP / GTM digest | `docs/brand/ICP-GTM.md` |
| GTM blueprint (md) | `docs/brand/gtm-blueprint.md` |
| Niche research raw | `docs/brand/niche-research.json` |
| Studio canvas snapshot | `docs/brand/studio-canvas.json` (empty) |
| Landing harness HTML | `docs/brand/landing-page-harness.html` |

## Share pack (`docs/brand/pdfs/`)

Majico-rendered from staging `download_export_zip` (except GTM blueprint — see note):

| File | Source |
|------|--------|
| `librebase-brand-guidelines.pdf` | Majico |
| `librebase-brand-profile.pdf` | Majico |
| `librebase-master-document.pdf` | Majico |
| `librebase-icp.pdf` | Majico (ICP / role research snapshot) |
| `librebase-gtm-blueprint.pdf` | Local render from `gtm-blueprint.md` — Majico ZIP omitted this until `gtm_blueprint` snapshot exists |

Copies also live at `docs/brand/*.pdf` for quick attach.

Re-download: Majico MCP `download_export_zip` on project `af1f6d03-4b45-4cb5-8276-548cfacd71ee` (staging).
Local GTM re-render: `python scripts/render_gtm_pdfs.py`
