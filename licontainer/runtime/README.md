# Container trusted surface (Li-only)

This directory documents the **upstream merge target** in `lic` — not local C sources.

Container `extern def` declarations live in:

`packages/li-container/src/seam.li`

Implementations are added to the **Li compiler repo** (`lic/runtime/`), following the `li-net` / `std/runtime/seam.li` pattern. See `docs/rfc-container-trusted-surface.md`.

**No `.c` or `.h` files belong in librebase.**
