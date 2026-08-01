# Majico export note

Downloaded 2026-07-30 / refreshed 2026-08-01.

| Artifact | Path |
|----------|------|
| Export ZIP contents | `docs/brand/majico-export/` |
| ICP / GTM digest | `docs/brand/ICP-GTM.md` |
| GTM blueprint (md) | `docs/brand/gtm-blueprint.md` |
| **GTM PDFs** | `docs/brand/gtm-pdfs/` |
| Niche research raw | `docs/brand/niche-research.json` |
| Studio canvas snapshot | `docs/brand/studio-canvas.json` (empty) |
| Landing harness HTML | `docs/brand/landing-page-harness.html` |

## GTM PDFs (`docs/brand/gtm-pdfs/`)

| File | Source |
|------|--------|
| `librebase-icp-gtm.pdf` | Rendered from `ICP-GTM.md` |
| `librebase-gtm-blueprint.pdf` | Rendered from `gtm-blueprint.md` |
| `librebase-brand-profile.pdf` | Majico export |
| `librebase-master-document.pdf` | Majico export |
| `librebase-brand-guidelines.pdf` | Majico export |

Re-render: `python scripts/render_gtm_pdfs.py`

**Note:** Majico Studio `gtm-strategy` / `gtm-jtbd` harness jobs were still processing/pending on staging (workers retrying; SearXNG returned 0). Local PDFs cover the completed niche-research GTM direction until Studio exports land.