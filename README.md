# Librebase

**Repository (origin):** [gitlab.lilangverse.xyz/librebase-official/librebase](https://gitlab.lilangverse.xyz/librebase-official/librebase) — [GitHub](https://github.com/librebase-official/librebase) is a read-only mirror.

**Librebase** is the open data platform powered by **lidb** — a Supabase-shaped stack with org/project/database workflows and a web console (**Librebase Studio**).

This repository is the canonical product home: platform code, Studio UI, docs, and Cursor agent rules.

## Brand (Figma)

The current **blue bird** identity is maintained in Figma. To sync logo and color tokens into Studio and docs, see [docs/brand/FIGMA.md](docs/brand/FIGMA.md).

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

## For AI agents (MCP)

Librebase exposes a hosted MCP endpoint — no local repo needed:

1. **Auto-discover:** `GET https://app.librebase.xyz/.well-known/mcp.json`
2. **Sign in:** device flow (`auth_start` / `auth_poll` on `POST https://app.librebase.xyz/api/mcp`) — a human approves once in the browser; the agent receives an `lb_agt_*` token.
3. **Connect:** send `Authorization: Bearer <token>` on every other tool call (`org_whoami`, `project_list`, `instance_list`, KMS tools, etc.).

Optional stdio bridge (repo checkout or future `librebase-mcp` package) — same contract as `@librebase/mcp`:

| Variable | Purpose |
|----------|---------|
| `LIBREBASE_MCP_URL` | Hosted MCP JSON-RPC URL (default `https://app.librebase.xyz/api/mcp`) |
| `LIBREBASE_MCP_TOKEN` | Optional `lb_mcp_*` / `lb_agt_*` bearer when skipping device flow |

```json
{
  "mcpServers": {
    "librebase": {
      "command": "python3",
      "args": ["-m", "librebase_mcp"],
      "env": {
        "LIBREBASE_MCP_URL": "https://app.librebase.xyz/api/mcp",
        "LIBREBASE_MCP_TOKEN": "lb_mcp_…"
      }
    }
  }
}
```

Details: [`mcp/README.md`](mcp/README.md) · https://app.librebase.xyz/for-agents · https://app.librebase.xyz/llms.txt

## Self-hosting

Run Studio, Admin API, and KMS on your own VM with Docker Compose. See [`docs/self-hosting.md`](docs/self-hosting.md) and [`deploy/compose/.env.example`](deploy/compose/.env.example).

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

**Local runtime without lidb:** Studio defaults to `LIDB_RUNTIME_MODE=dev`, which starts `scripts/dev_runtime_stub.py` via `scripts/lidb_engine.py` when `LIDB_ROOT` is unset.

**Production local runtime:** set `LIDB_ROOT` to a lidb checkout and ensure `lis` is on `PATH`.

## Kubernetes

Studio can target a Kubernetes cluster instead of local processes:

```powershell
$env:LIBREBASE_RUNTIME = "kubernetes"
$env:KUBECONFIG = "C:\path\to\kubeconfig"
```

| Path | Purpose |
|------|---------|
| `deploy/docker/lidb-runtime/` | Dev runtime Docker image (`librebase/lidb-runtime:dev`) |
| `deploy/kubernetes/` | Reference manifests (dedicated + shared) |
| `deploy/helm/librebase-instance/` | Helm chart for manual installs |
| `docs/kubernetes.md` | Architecture, kind/minikube steps, Studio flow |
| `data-studio-ui/lib/k8s-provisioner.ts` | Provisioner used by API and launch routes |

Build the runtime image, load into kind/minikube, then create a project with **Deploy to Kubernetes** on `/projects/new` (or set `LIBREBASE_RUNTIME=kubernetes` globally):

```powershell
.\deploy\docker\lidb-runtime\build.ps1
kind load docker-image librebase/lidb-runtime:dev --name librebase
$env:LIBREBASE_K8S_IMAGE = "librebase/lidb-runtime:dev"
```

Health stays honest: green only when probes see real open ports.

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
| lidb embed / dev runtime | Python unittest | `lidb_engine.py` lifecycle, port probes |
| E2E | Playwright (planned) | create flow, Instances view, honest health UI |

```powershell
cd data-studio-ui && npm test
python -m unittest discover -s tests -p "test_*.py"
```

GitHub Actions (`.github/workflows/test.yml`) runs on push and PR to `main`: Vitest + Python tests + `npm run build` in `data-studio-ui` (Node 20).

## licontainer (Li Container Engine)

**Pure Li** OCI engine — `licontainer/` contains only `.li` packages. No Rust, no C in librebase. Trusted OCI impl merges into `lic` (like `li-net`).

```bash
export LIC_ROOT=/path/to/lic
./licontainer/scripts/build-li.sh
```

| Path | Purpose |
|------|---------|
| `licontainer/packages/` | Li workspace: run, daemon, CLI, img, cri |
| `licontainer/PURE-LI-POLICY.md` | Repo language policy |
| `docs/rfc-container-trusted-surface.md` | Upstream `lic` merge RFC |

Studio: `LIBREBASE_RUNTIME=licontainer`. K8s: Helm `containerRuntime: licontainer`.

CI: `.github/workflows/licontainer-build.yml` (pure Li `lic build` only).
