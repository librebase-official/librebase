# Kubernetes runtime

Librebase Studio can provision instance runtimes on Kubernetes instead of local `lis db start`. The control plane lives in `data-studio-ui/lib/k8s-provisioner.ts`; manifests are generated in `k8s-manifests.ts` and applied with `kubectl`.

## Prerequisites

| Requirement | Purpose |
|-------------|---------|
| `kubectl` on PATH | Apply and status queries |
| `KUBECONFIG` (or default kube context) | Cluster credentials |
| Cluster with default StorageClass | PVC for `LI_DATA_DIR` |
| Runtime image (see below) | Dev stub or production `lis` + lidb in pod |

Set Studio runtime target:

```powershell
$env:LIBREBASE_RUNTIME = "kubernetes"
$env:KUBECONFIG = "C:\path\to\kubeconfig"
cd data-studio-ui
npm run dev
```

Per-request override: pass `"runtime": "kubernetes"` on `POST /api/instances` or `POST /api/projects`.

## Architecture

```mermaid
flowchart LR
  studio[Studio API]
  prov[k8s-provisioner]
  kubectl[kubectl apply]
  cluster[K8s cluster]
  studio --> prov --> kubectl --> cluster
```

### Dedicated (1 instance : 1 project)

- Namespace: `librebase-inst-<instanceId>`
- Full stack: PVC, ConfigMap, Secret, Deployment, Service
- Labels: `librebase.io/org`, `librebase.io/instance`, `librebase.io/deployment-mode=dedicated`

### Shared (1 instance : N projects)

- Namespace: `librebase-shared-<orgId>`
- One Deployment/PVC/Service per instance
- Each project gets a ConfigMap (`librebase-project-<projectId>`) with schema namespace metadata

## Health and honest degraded mode

- **Liveness:** exec `lidb_engine.py status` (same JSON contract as local `scripts/lidb_engine.py`)
- **Readiness:** TCP on API port
- Status JSON includes `running`, `api_reachable`, `postgres_reachable`, and `runtime_mode` (`dev` | `production` | `unavailable`)
- `running: true` only when both API and postgres-wire ports accept TCP connections
- If `kubectl cluster-info` fails → `degraded: true`, status `stopped` — Studio never shows fake green

## Container image

Build the dev runtime image from the repo root:

```powershell
.\deploy\docker\lidb-runtime\build.ps1
```

```bash
./deploy/docker/lidb-runtime/build.sh
```

Default tag: **`librebase/lidb-runtime:dev`**

Override in Studio: `LIBREBASE_K8S_IMAGE`. The image ships:

- `lidb_engine.py` and `dev_runtime_stub.py` at `/opt/librebase/scripts/`
- `entrypoint.sh` — starts `lis db start` when `LIDB_ROOT` + `lis` exist, otherwise dev stub when `LIDB_RUNTIME_MODE=dev`
- Writable `/data` mount (`LI_DATA_DIR`)

Production image (future): same layout with real `lis` + lidb embed and `LIDB_RUNTIME_MODE=production`.

## Studio integration

| Action | Behavior |
|--------|----------|
| Create project + "Deploy to Kubernetes" | Creates instance with `runtimeTarget: kubernetes`, calls `provisionDedicatedInstance` |
| Shared project on K8s instance | `attachSharedProject` applies project ConfigMap |
| Launch instance/project | Re-applies manifests, then `getInstanceStatus` |
| `/instances` UI | Shows `runtimeTarget`, namespace, pod phase, **dev runtime** vs **production** badge |
| `GET /api/instances/:id/status` | Local or K8s probe |

Local launch without `LIDB_ROOT` defaults to `LIDB_RUNTIME_MODE=dev` via `project-runtime.ts`.

## Entitlements

K8s provisioning and launch paths include `TODO` entitlement gates (paid Studio/lidb). Wire plan/license checks before removing TODOs.

## Manual deploy (without Studio)

**Helm (dedicated):**

```powershell
helm install my-instance deploy/helm/librebase-instance `
  --set instanceId=inst_manual `
  --set orgId=default `
  --set deploymentMode=dedicated
```

**Raw manifests:** see `deploy/kubernetes/`.

## Local cluster quickstart (kind)

```powershell
kind create cluster --name librebase

# Build and load the dev runtime image into kind
.\deploy\docker\lidb-runtime\build.ps1
kind load docker-image librebase/lidb-runtime:dev --name librebase

$env:KUBECONFIG = "$env:USERPROFILE\.kube\config"
$env:LIBREBASE_RUNTIME = "kubernetes"
$env:LIBREBASE_K8S_IMAGE = "librebase/lidb-runtime:dev"
cd data-studio-ui
npm run dev
```

Create a project with **Deploy to Kubernetes** checked. Studio applies manifests; the pod should reach **Running** and **Ready** once the dev runtime binds API (54320) and postgres (54322) ports.

### Verify green health on kind

```powershell
# After provisioning an instance in Studio:
kubectl get pods -A -l app.kubernetes.io/name=librebase-instance
kubectl get pods -n librebase-inst-<instanceId> -o wide

# Pod should show 1/1 Ready; liveness uses lidb_engine.py status
kubectl exec -n librebase-inst-<instanceId> deploy/librebase-runtime -- \
  python3 /opt/librebase/scripts/lidb_engine.py status --data-dir /data --api-port 54320 --postgres-port 54322

# Expect JSON with "status":"running", "running":true, "runtime_mode":"dev"
```

### minikube

```powershell
minikube start
.\deploy\docker\lidb-runtime\build.ps1
minikube image load librebase/lidb-runtime:dev
$env:KUBECONFIG = "$env:USERPROFILE\.kube\config"
# same Studio steps as kind
```

Optional: `kubectl port-forward -n librebase-inst-<id> svc/librebase-api 54320:54320` for local API access.

## CI

Vitest mocks `kubectl` — no cluster in GitHub Actions. Python `unittest` covers `lidb_engine.py` dev mode and port probes without Docker. Optional kind job can be added later.

## Related

- `docs/architecture-instances.md` — instance/project model
- `deploy/kubernetes/README.md` — manifest reference
- `deploy/docker/lidb-runtime/README.md` — image build
- `data-studio-ui/lib/k8s-provisioner.ts` — provisioner API
