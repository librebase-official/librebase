# licontainer — Li Container Engine

General-purpose OCI-compatible container engine for Librebase. **All engine code is Li (`.li`) — no Rust.**

Low-level isolation uses the **Li trusted runtime seam** (`runtime/seam-container.li` + `li_rt_container.c`), the same model as `std/runtime/seam.li` for networking in `lic`. Application logic, daemon, CLI, CRI, and image store are Li packages under `licontainer/packages/`.

> The Rust crates (`lirun/`, `lictl/`, …) are **deprecated** — see [`licontainer/DEPRECATED-RUST.md`](../licontainer/DEPRECATED-RUST.md).

## Architecture

```mermaid
flowchart TB
  subgraph studio [Librebase Studio]
    Prov[licontainer-provisioner]
  end

  subgraph licontainer [licontainer stack]
    Lictl[lictl CLI]
    Daemon[licontainerd]
    CRI[licri CRI shim]
    Run[lirun OCI runtime]
    Img[liimg image store]
  end

  Prov --> Lictl
  Lictl --> Daemon
  CRI --> Daemon
  Daemon --> Run
  Daemon --> Img
  Kubelet[kubelet] --> CRI
```

| Component | Li package | Role |
|-----------|------------|------|
| `lirun` | `packages/li-container-run/` | OCI runtime: create/start/delete/kill/state |
| `licontainerd` | `packages/li-containerd/` | Daemon: images, containers, Unix socket JSON API |
| `lictl` | `packages/li-container-cli/` | Docker-like CLI: pull, run, ps, stop |
| `liimg` | `packages/li-container-img/` | OCI layout pull/store, optional squashfs export |
| `licri` | `packages/li-container-cri/` | Kubernetes CRI v1 subset |
| Core types | `packages/li-container/` | Shared library |
| Trusted OCI seam | `runtime/seam-container.li` | Namespaces, cgroups, seccomp (Li extern model) |

## OCI compliance matrix (v1)

| Spec operation | Status | Notes |
|----------------|--------|-------|
| `config.json` bundle | ✅ | process, root, mounts, linux namespaces, cgroups |
| `create` | ✅ Li | `li-container-run` + `li_rt_container.c`; Linux only |
| `start` | ✅ Li | namespaces + pivot_root via trusted seam |
| `delete` | ✅ Li | `--force` for running |
| `kill` | ✅ Li | SIGTERM/SIGKILL |
| `state` | ✅ Li | JSON on stdout |
| checkpoint | ❌ | deferred |
| hooks (all types) | ❌ | deferred |
| events | ❌ | deferred |

## Security model

- **Rootless-by-default**: drop all capabilities; bundle may add `NET_BIND_SERVICE` etc.
- **Seccomp**: deny-all + syscall whitelist via `container_seccomp_apply_i` trusted seam
- **No privileged API**: daemon rejects privileged containers (no `--privileged` in API)
- **Socket permissions**: `licontainerd.sock` and `licri.sock` created with mode `0600`
- **Entitlement gates**: `check_entitlement()` TODO before `PullImage` / `CreateContainer` for Librebase cloud
- **Optional signature verify**: set `LI_CONTAINER_REQUIRE_SIGNATURE=1` (future Cosign integration)

## Windows WSL2 bridge (v1)

Native Windows containers (HCS/runhcs) are **out of v1 scope**.

On Windows, `lictl` forwards to a WSL2 distro:

```powershell
# Install (creates LibrebaseContainer distro)
.\deploy\windows\install-licontainer-wsl.ps1

# Run via WSL bridge
lictl run hello-world
```

Environment:

| Variable | Default | Purpose |
|----------|---------|---------|
| `LI_CONTAINER_WSL_DISTRO` | `LibrebaseContainer` | WSL distro name |

## Building (Li)

Requires a `lic` compiler checkout (`LIC_ROOT` or `lic` on PATH):

```bash
export LIC_ROOT=/path/to/lic
./licontainer/scripts/build-li.sh
```

Build individual binaries:

```bash
lic build licontainer/packages/li-container-cli/src/main.li -o lictl
lic build licontainer/packages/li-container-run/src/main.li -o lirun
```

### Phase 1 lirun (Li) — Rust parity

| Rust (`lirun/`) | Li (`packages/`) |
|-----------------|------------------|
| `main.rs` CLI | `li-container-run/src/main.li` |
| `bundle.rs` | `li-container/src/bundle.li` + `state.li` |
| `runtime.rs` | `li-container-run/src/runtime.li` |
| `error.rs` | `li-container/src/error.li` |
| `seccomp.rs` | `runtime/li_rt_container.c` (`container_seccomp_apply_i`) |

Trusted runtime: link `runtime/li_rt_container.c` into `lic` (see `runtime/CMakeLists.txt`) and merge `runtime/seam-container.li` into `std/runtime/seam.li` upstream.

```bash
# OCI lifecycle (Linux / WSL2)
export LI_CONTAINER_STATE_DIR=/run/licontainer/containers
lirun create --bundle /path/to/bundle --id myctr
lirun start --id myctr
lirun state --id myctr          # JSON on stdout
lirun kill --id myctr SIGTERM
lirun delete --id myctr --force
lirun version
```

Integration test (requires root/CAP_SYS_ADMIN):

```bash
LI_CONTAINER_INTEGRATION=1 licontainer/scripts/test-lirun-integration.sh
```

Build requirements: `lic` compiler with trusted extern support; on Linux optionally `libseccomp` (`LI_CONTAINER_SKIP_SECCOMP=1` to skip). Non-Linux returns `UNSUPPORTED` JSON error.

### Deprecated Rust build

Rust crates remain temporarily for reference only:

```bash
cd licontainer && cargo build   # deprecated — do not extend
```

See [`DEPRECATED-RUST.md`](../licontainer/DEPRECATED-RUST.md).

## Running lictl

```bash
# Start daemon (Linux / WSL2)
licontainerd --socket /run/licontainer/licontainerd.sock

# Pull and run
lictl pull ghcr.io/librebase-official/lidb-runtime:dev
lictl run --name mydb ghcr.io/librebase-official/lidb-runtime:dev
lictl ps
lictl stop <container-id>
```

Environment:

| Variable | Default | Purpose |
|----------|---------|---------|
| `LI_CONTAINER_SOCKET` | `/run/licontainer/licontainerd.sock` | Daemon socket |
| `LI_CONTAINER_STORE` | `/var/lib/licontainer` | Image/container store |
| `LI_CONTAINER_STATE_DIR` | `/run/licontainer/containers` | lirun state |
| `LI_CONTAINER_CGROUP_ROOT` | `/sys/fs/cgroup/licontainer` | cgroup v2 root |
| `LIRUN_BIN` | `lirun` | Runtime binary path |

## Kubernetes

```bash
# Node bootstrap
sudo deploy/kubernetes/node-bootstrap/install-licontainer.sh

# Apply RuntimeClass
kubectl apply -f deploy/kubernetes/runtime-class-licontainer.yaml

# Helm with licontainer runtime
helm install myinst deploy/helm/librebase-instance \
  --set containerRuntime=licontainer
```

Kubelet config: `container-runtime-endpoint=unix:///run/licontainer/licri.sock`

## Benchmarks

See `benchmarks/licontainer-vs-docker/README.md` for RSS and cold-start comparison scripts.

## Security checklist

- [ ] Containers run without CAP_SYS_ADMIN
- [ ] Seccomp profile active (`LI_CONTAINER_STRICT_SECCOMP=1` in prod)
- [ ] Root filesystem read-only where bundle specifies `readonly: true`
- [ ] cgroup v2 limits applied (pids.max default 256)
- [ ] Daemon socket mode 0600
- [ ] No privileged flag in daemon API
- [ ] Entitlement check before pull/create in cloud (TODO)

## lidb production image

Export lidb-runtime as OCI + squashfs:

```bash
scripts/export-lidb-oci-image.sh
```

Default K8s image: `ghcr.io/librebase-official/lidb-runtime:oci-squashfs` (see `k8s-manifests.ts`).
