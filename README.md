# Librebase

**Repository:** [github.com/librebase-official/librebase](https://github.com/librebase-official/librebase) (private)

**Librebase** is the open data platform powered by **lidb** — a Supabase-shaped stack with org/project/database workflows and a web console (**Librebase Studio**).

This repository is the canonical product home: platform code, Studio UI, docs, and Cursor agent rules.

## Paid features

**lidb** and **Librebase Studio** are monetized product surfaces. Billing/entitlement enforcement is planned; launch paths include TODO gates in `project-runtime.ts`. See `.cursor/rules/librebase-product.mdc` for agent guidance.

## Repository layout

| Path | Purpose |
|------|---------|
| `data-studio-ui/` | Platform and Studio UI (Next.js) |
| `scripts/` | lidb embed lifecycle (`lidb_engine.py`) |
| `docs/` | Architecture and CLI/database docs |
| `.cursor/rules/` | Cursor agent product context |

## Instance & project model

Librebase supports **dedicated** (1 instance → 1 project, default) and **shared** (1 instance → N projects) deployment. See `docs/architecture-instances.md`.

Studio persistence (instances + projects JSON) lives under:

- **Linux/macOS:** `~/.local/share/librebase/studio`
- **Windows:** `%LOCALAPPDATA%\librebase\studio`

Override with `LIBREBASE_STUDIO_DATA_DIR`.

## Development

From the repo root:

```powershell
cd data-studio-ui
npm install
npm run dev
```

Studio dev server: [http://127.0.0.1:54324](http://127.0.0.1:54324)

Cloud workflow routes:

| Route | Purpose |
|-------|---------|
| `/` | Projects grid (primary nav) |
| `/instances` | Instances list + health |
| `/projects/new` | Create project (new instance vs existing) |
| `/projects/:id` | Project home + launch database |

Optional: set `LIDB_ROOT` to a lidb checkout and ensure `lis` is on `PATH` for non-degraded launch via `scripts/lidb_engine.py`.

## Testing

```powershell
cd data-studio-ui
npm test
```

| Layer | Tool | Focus |
|-------|------|-------|
| Studio stores / bridge | Vitest | `instances-store`, `projects-store`, dedicated vs shared |
| lidb embed | pytest (planned) | `lidb_engine.py` lifecycle |
| E2E | Playwright (planned) | create flow, Instances view, honest health UI |

CI (GitHub Actions) for lint + unit on PR is planned.
