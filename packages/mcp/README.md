# Librebase MCP

Agent control surface for **Librebase Admin API**, Studio probes, and the Wave A parity harness.

## Install

```bash
cd packages/mcp
npm install
```

## Cursor config

Add to Cursor MCP settings (project or user):

```json
{
  "mcpServers": {
    "librebase": {
      "command": "node",
      "args": [
        "C:/Users/Julian/Documents/Programming/librebase/packages/mcp/src/server.js"
      ],
      "env": {
        "LIBREBASE_ADMIN_URL": "http://127.0.0.1:54330",
        "LIBREBASE_ROOT": "C:/Users/Julian/Documents/Programming/librebase"
      }
    }
  }
}
```

Start Admin API first:

```bash
python admin-api/scripts/admin_server.py
# or: node packages/cli/src/index.js start:admin
```

## Tools

| Tool | Action |
|------|--------|
| `admin_health` | `/health` |
| `admin_setup` | First-run org (stores session) |
| `admin_login` | Session JWT (stored in-memory for later tools) |
| `auth_status` | Report admin/project session + active org |
| `admin_logout` | Clear in-memory admin session |
| `set_project_session` | Store a project API bearer token for project tools |
| `list_projects` / `list_instances` | Org metadata (orgId defaults to session) |
| `create_host` / `list_hosts` / `get_host` | Rent/manage VMs (memMb budget) |
| `create_instance` / `create_project` | Metadata CRUD (place instance on a host) |
| `studio_probe` | Studio HTTP liveness |
| `runtime_status` | `lidb_engine.py status` |
| `parity_run` | Wave A `parity_runner.py` |
| `check_entitlement` | Feature gate |
| `matrix_status` | Count ✅/🚧/⬜/❌ + last harness report |
| `execute_sql` / `list_tables` / `list_storage_buckets` | Project API (fail closed) |
| `sign_storage_url` / `auth_otp` | Storage sign + magiclink OTP |
| `get_project_url` / `get_publishable_keys` | Env-backed meta (honest stubs) |
| `list_edge_functions` / auth admin / `apply_migration` / `get_logs` | Lean Supabase-MCP-shaped |

## Auth

After `admin_setup` / `admin_login`, the returned token and `orgId` are stored **in-memory**
for the MCP process, so subsequent admin tools authenticate automatically — no manual
`LIBREBASE_ADMIN_SESSION` env needed. `auth_status` reports the session; `admin_logout`
clears it. Project tools (`execute_sql`, storage, auth admin) use a project bearer token
from `set_project_session` (or the per-call `bearer` arg). Tokens are per-process and are
not persisted to disk.

## Smoke

```bash
node packages/mcp/scripts/smoke.mjs   # tool surface only
npm test                              # smoke + live e2e (spawns Admin API)
```

Parity DoD (Admin up): `admin_setup` → `create_host` → `create_instance` → `create_project` → `list_projects` → `parity_run` → `matrix_status`.
