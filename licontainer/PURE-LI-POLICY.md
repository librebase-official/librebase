# Pure Li policy — licontainer

**librebase contains only Li source for the container engine.**

| Allowed in `licontainer/` | Not allowed in `librebase` |
|---------------------------|----------------------------|
| `.li` modules | Rust (`.rs`, `Cargo.toml`) |
| `li.toml` packages | C/C++ (`.c`, `.h`) |
| `lic build` scripts | Python engine code for licontainer |
| Li `extern proc` declarations | Vendored syscall shims |

## Trusted runtime

OCI isolation (`unshare`, cgroups, `pivot_root`, seccomp) is declared as **`extern proc` in Li** (`packages/li-container/src/seam.li`) and implemented in the **`lic` compiler runtime** (`lic/runtime/`), merged into `std/runtime/seam.li` — same model as `Net` / `li-net`.

No C files live in librebase. Upstreaming container externs into `lic` is required before `lirun` links on a real host.

## Build

```bash
export LIC_ROOT=/path/to/lic
./licontainer/scripts/build-li.sh
```

Windows: `.\licontainer\scripts\build-li.ps1`
