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
| `admin_setup` | First-run org |
| `admin_login` | Session JWT (set `LIBREBASE_ADMIN_SESSION` for later tools) |
| `list_projects` / `list_instances` | Org metadata |
| `create_instance` / `create_project` | Metadata CRUD |
| `studio_probe` | Studio HTTP liveness |
| `runtime_status` | `lidb_engine.py status` |
| `parity_run` | Wave A `parity_runner.py` |
| `check_entitlement` | Feature gate |
| `matrix_status` | Count ✅/🚧/⬜/❌ + last harness report |
| `execute_sql` / `list_tables` / `list_storage_buckets` | Project API (fail closed) |
| `sign_storage_url` / `auth_otp` | Storage sign + magiclink OTP |
| `get_project_url` / `get_publishable_keys` | Env-backed meta (honest stubs) |
| `list_edge_functions` / auth admin / `apply_migration` / `get_logs` | Lean Supabase-MCP-shaped |

After `admin_setup` / `admin_login`, put the returned `token` in `LIBREBASE_ADMIN_SESSION` for authenticated calls (or restart MCP with that env).

## Smoke

```bash
node packages/mcp/scripts/smoke.mjs
```

Parity DoD (Admin up): `admin_setup` → `create_instance` → `create_project` → `list_projects` → `parity_run` → `matrix_status`.
