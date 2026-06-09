# Trusted runtime seam for Li Container Engine (OCI isolation).

OCI syscalls (namespaces, cgroups, mount, seccomp) are **Li trusted externs** —
same model as `std/runtime/seam.li` for networking in `lic`.

Product `.li` code imports `container.seam` (re-exported from `packages/li-container`).
Implementations live in `li_rt_container.c` and register via
`security/trusted-extern-manifest.toml` in the `lic` compiler tree (upstream merge)
or a pinned `LIC_ROOT` overlay during development.

## Extern surface (Phase 1)

| Extern | Role |
|--------|------|
| `container_unshare_i` | Linux namespaces |
| `container_cgroup_create_i` | cgroup v2 directory |
| `container_cgroup_apply_limits_i` | memory/cpu/pids limits from bundle JSON |
| `container_fork_child_i` | fork for start |
| `container_setup_rootfs_i` | mounts + pivot_root |
| `container_exec_i` | execve process args from bundle |
| `container_kill_i` | signal container pid |
| `container_seccomp_apply_i` | deny-all + whitelist (libseccomp optional) |
| `container_state_write_i` | OCI state.json |
| `container_mkdir_p_i` | state/cgroup paths |

## Build

Standalone static library (dev):

```bash
./licontainer/scripts/build-runtime-c.sh
```

CMake (upstream into `lic/runtime`):

```bash
cmake -S licontainer/runtime -B build-container-rt
cmake --build build-container-rt
```

Append to `lic/runtime/CMakeLists.txt`:

```cmake
list(APPEND LI_RT_SOURCES ${CMAKE_SOURCE_DIR}/../librebase/licontainer/runtime/li_rt_container.c)
```

No Rust. No raw syscalls in application `.li` modules.
