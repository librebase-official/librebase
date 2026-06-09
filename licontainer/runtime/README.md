# Trusted runtime seam for Li Container Engine (OCI isolation).

OCI syscalls (namespaces, cgroups, mount, seccomp) are **Li trusted externs** —
same model as `std/runtime/seam.li` for networking in `lic`.

Product `.li` code imports `container.runtime.seam` (re-exported from packages).
Implementations live in `li_rt_container.c` and register via
`security/trusted-extern-manifest.toml` in the `lic` compiler tree (upstream merge)
or a pinned `LIC_ROOT` overlay during development.

## Planned extern surface (v1)

| Extern | Role |
|--------|------|
| `container_unshare_i` | Linux namespaces |
| `container_cgroup_apply_i` | cgroups v2 limits |
| `container_pivot_root_i` | rootfs pivot |
| `container_seccomp_apply_i` | default deny-all profile |
| `container_state_json_i` | OCI state JSON for `lirun state` |

No Rust. No raw syscalls in application `.li` modules.
