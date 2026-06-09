# DEPRECATED — Rust licontainer (remove after Li parity)

The **Li Container Engine is Li-only**. The Rust crates in this directory
(`lirun/`, `licontainerd/`, `lictl/`, `liimg/`, `licri/`, `licontainer-proto/`)
were an interim scaffold and **must not be extended**.

| Canonical (Li) | Deprecated (Rust) |
|----------------|-------------------|
| `packages/li-container-run/` | `lirun/` |
| `packages/li-containerd/` | `licontainerd/` |
| `packages/li-container-cli/` | `lictl/` |
| `packages/li-container-img/` | `liimg/` |
| `packages/li-container-cri/` | `licri/` |
| `runtime/seam-container.li` | `lirun/src/seccomp.rs`, etc. |

Build Li packages with `scripts/build-li.sh` and `LIC_ROOT` pointing at a `lic` checkout.

Rust CI remains temporarily with `continue-on-error: true` until Li parity lands.
