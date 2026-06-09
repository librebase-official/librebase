# RFC: Trusted `Container` surface for licontainer (Li-only)

**Status:** proposed — merge into `lic` before production `lirun` links.

## Goal

Like `Net` for `li-net-httpd`, container isolation is a **trusted Li effect**. User `.li` code in librebase proves against abstract ops; the audited implementation lives in **`lic/runtime/`** only.

## Li declarations (librebase)

`licontainer/packages/li-container/src/seam.li` — `extern proc container_* raises Container`

## Implementation (lic repo only)

| File | Role |
|------|------|
| `lic/std/runtime/seam.li` | merge container extern block |
| `lic/runtime/li_rt_container.c` | audited syscall shim |
| `lic/docs/semantics/trusted.lean` | Container axiom family |
| `lic/li-tests/container_trusted/` | effect policy tests |

## Forbidden

- C/Rust/Python syscall code in `librebase-official/librebase`
- Raw `extern proc` in application modules outside `seam.li`

## Exit gate

- [ ] Container row in `trusted.lean`
- [ ] `lic build` links `lirun` on Linux with merged seam
- [ ] Rust removed from librebase (done)
- [ ] C removed from librebase (done)
