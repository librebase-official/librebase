# Librebase Admin API — pure Li

Li control plane for Librebase Studio. Same HTTP surface as
`admin-api/scripts/admin_server.py` (drop-in swap).

**Status:** scaffold + `/health` + route dispatch table. Auth/org CRUD still
served by the Python interim until lidb seam + JWT/crypto paths land.

## Layout

| Path | Role |
|------|------|
| `src/seam.li` | Trusted externs (net TCP/HTTP + lidb embed) |
| `src/routes.li` | Path classifiers matching `/org/v1/*` |
| `src/health.li` | `GET /health` JSON body builder |
| `src/admin_server.li` | Listen loop (port 54330) |
| `li-tests/smoke/builds.li` | Compile smoke |

## Build

From repo root (preferred):

```bash
export LIC_ROOT=/path/to/lic   # default: ../lic sibling
chmod +x admin-api/li/scripts/build-li.sh
admin-api/li/scripts/build-li.sh
# → admin-api/li/build/admin_server when lic is available
```

If `lic` is missing at `LIC_ROOT`, the script lists `*.li` sources and exits 0
(syntax smoke only).

Requires sibling `lic` with KMS/net runtime externs (same as li-kms) when
building a binary:

```bash
export LI_NATIVE_RT=1
export LI_RT_LIB="$LIC_ROOT/build-mac/runtime/libli_rt.a"   # or Linux build dir
```

## CI

Workflow [`.github/workflows/admin-api-li.yml`](../../.github/workflows/admin-api-li.yml)
on changes under `admin-api/li/**` or `tests/admin_contract/**`:

1. Checkout `li-langverse/lic` into `lic/` (same pattern as licontainer-build)
2. Run `admin-api/li/scripts/build-li.sh`
3. Always run Python `tests.admin_contract.test_health`
4. When `admin-api/li/build/admin_server` exists, run full contract suite with
   `LIBREBASE_ADMIN_CONTRACT_LI=1`

## Run (Li)

```bash
./admin_server   # listens 54330 — GET /health → 200 {"ok":true,"service":"librebase-admin","runtime":"li"}
```

## Run (interim Python)

```bash
python admin-api/scripts/admin_server.py
```

## Port checklist (route families)

Tracked in **[docs/superpowers/plans/2026-10-18-li-admin-api-port.md](../../docs/superpowers/plans/2026-10-18-li-admin-api-port.md)** (LIB-133).

- [x] Package layout + seam stubs
- [x] `GET /health`
- [x] Contract harness + CI (`tests/admin_contract`, `admin-api-li.yml`)
- [ ] `POST /org/v1/setup` + SQLite/lidb migrations (LIB-135)
- [ ] Auth (login/refresh/logout/MFA/OAuth) (LIB-136)
- [ ] Org projects / instances / hosts CRUD
- [ ] MCP keys + usage
- [ ] Stripe billing webhook/session/portal
- [ ] `LIBREBASE_ADMIN_REQUIRE_LI=1` dual-run gate in deploy

Keep JSON field names identical to the Python handler so Studio needs no fork.
