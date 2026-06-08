# lidb-runtime container image

Runnable dev runtime for Librebase instances on Kubernetes (kind, minikube) and local Docker.

## Build

```powershell
.\deploy\docker\lidb-runtime\build.ps1
```

```bash
./deploy/docker/lidb-runtime/build.sh
```

Default tag: `librebase/lidb-runtime:dev` (override with `LIBREBASE_RUNTIME_IMAGE`).

## Behavior

| `LIDB_ROOT` + `lis` | `LIDB_RUNTIME_MODE` | Process |
|---------------------|---------------------|---------|
| Present | any | `lis db start` (production) |
| Missing | `dev` (default) | `dev_runtime_stub.py` — HTTP on API port, TCP on postgres port |
| Missing | other | Exit 1 |

Health probes use `lidb_engine.py status` (liveness) and TCP on the API port (readiness).

## Load into kind

```powershell
kind load docker-image librebase/lidb-runtime:dev --name librebase
```

Set Studio image override if needed:

```powershell
$env:LIBREBASE_K8S_IMAGE = "librebase/lidb-runtime:dev"
```
