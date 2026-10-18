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

Requires sibling `lic` with KMS/net runtime externs (same as li-kms):

```bash
export LIC_ROOT=/path/to/lic
export LI_NATIVE_RT=1
export LI_RT_LIB="$LIC_ROOT/build-mac/runtime/libli_rt.a"   # or Linux build dir
# from repo root or this directory once lic flatten supports package roots:
lic build admin-api/li/src/admin_server.li
```

## Run (Li)

```bash
./admin_server   # listens 54330 — GET /health → 200 {"ok":true,"service":"librebase-admin","runtime":"li"}
```

## Run (interim Python)

```bash
python admin-api/scripts/admin_server.py
```

## Port checklist (route families)

- [x] Package layout + seam stubs
- [x] `GET /health`
- [ ] `POST /org/v1/setup` + SQLite/lidb migrations
- [ ] Auth (login/refresh/logout/MFA/OAuth)
- [ ] Org projects / instances / hosts CRUD
- [ ] MCP keys + usage
- [ ] Stripe billing webhook/session/portal
- [ ] `LIBREBASE_ADMIN_REQUIRE_LI=1` dual-run gate in deploy

Keep JSON field names identical to the Python handler so Studio needs no fork.
