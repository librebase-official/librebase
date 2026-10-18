---
name: librebase-li-port
description: Continue or audit the pure-Li port of Librebase backend (Admin API, lidb seam, li-httpd). Frontend may stay JS. Use when implementing admin-api/li, src/seam.li, or Li port status reports.
---

# Librebase Li backend port

## Mandate

From `docs/sdd/specs/cloud-ga/PLAN.md`:

| Surface | Li home |
|---------|---------|
| Control plane | `admin-api/li/` + `src/seam.li` |
| KMS | sibling `li-kms` (not grow `kms/` Python) |
| HTTP | li-httpd / runtime `tcp_*` externs |
| DB | lidb embed via seam |

Studio/Next.js stays JS.

## Working rules

- Keep HTTP paths + JSON shapes stable vs `admin-api/scripts/admin_server.py`.
- Python shim remains default until smoke proves Li path.
- Env `LIBREBASE_ADMIN_REQUIRE_LI=1` fails closed if Li binary missing (when wired).
- Pure Li: `def` only; trusted FFI in `seam.li` / `admin-api/li/src/seam.li`.
- Port by route family: health → setup/auth → org CRUD → billing → hosts.

## Verify

```bash
# Li package smoke (needs lic + runtime)
# See admin-api/li/README.md
python -m unittest tests.test_admin_api   # Python shim still green
```
