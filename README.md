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

## Kubernetes

Studio can target a Kubernetes cluster instead of local processes:

```powershell
$env:LIBREBASE_RUNTIME = "kubernetes"
$env:KUBECONFIG = "C:\path\to\kubeconfig"
```

| Path | Purpose |
|------|---------|
| `deploy/kubernetes/` | Reference manifests (dedicated + shared) |
| `deploy/helm/librebase-instance/` | Helm chart for manual installs |
| `docs/kubernetes.md` | Architecture, kind/minikube steps, Studio flow |
| `data-studio-ui/lib/k8s-provisioner.ts` | Provisioner used by API and launch routes |

Create a project with **Deploy to Kubernetes** on `/projects/new`, or set `LIBREBASE_RUNTIME=kubernetes` globally. Health stays honest when the cluster or runtime image is unavailable.

## Testing

```powershell
cd data-studio-ui
npm test
npm run test:coverage
```

`test:coverage` reports line coverage for `lib/**` (30% line threshold locally). CI runs the same report without failing on coverage thresholds while the suite grows.

| Layer | Tool | Focus |
|-------|------|-------|
| Studio stores / bridge | Vitest | `instances-store`, `projects-store`, dedicated vs shared |
| lidb embed | pytest (planned) | `lidb_engine.py` lifecycle |
| E2E | Playwright (planned) | create flow, Instances view, honest health UI |

GitHub Actions (`.github/workflows/test.yml`) runs on push and PR to `main`: `npm ci`, `npm test`, optional coverage report, and `npm run build` in `data-studio-ui` (Node 20).
