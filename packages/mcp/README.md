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

After `admin_setup` / `admin_login`, put the returned `token` in `LIBREBASE_ADMIN_SESSION` for authenticated calls (or restart MCP with that env).

## Smoke

```bash
node packages/mcp/scripts/smoke.mjs
```

Parity DoD (Admin up): `admin_setup` → `create_instance` → `create_project` → `list_projects` → `parity_run` → `matrix_status`.
