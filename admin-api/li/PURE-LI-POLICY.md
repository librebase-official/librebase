# Pure Li policy — `admin-api/li/`

This tree is **`.li` only**. No Python, Rust, or C sources here.

- Use `def` only (no `proc`).
- Trusted FFI is declared in `src/seam.li` (`extern def`) and implemented in
  upstream `lic` runtime / lidb — same pattern as `licontainer/` and `li-kms`.
- The Python shim under `admin-api/scripts/` is interim and lives outside this tree.
