# Librebase Supabase-parity execution plan

**North star:** Full Supabase vertical parity on linative stack (**lidb** + **lis** + opt-in packages), with Librebase as the **product** (Studio Admin, CLI, Cloud compose) — not a fork of lis/lidb.

**SDD (authoritative for core vertical):** [docs/sdd/specs/supabase-parity/](sdd/specs/supabase-parity/) (`requirements.md`, `spec.md`, `tasks.md`) · Constitution: [docs/sdd/CONSTITUTION.md](sdd/CONSTITUTION.md) · Pins: [li-dependency-pins.md](li-dependency-pins.md)

**Order (non-negotiable):**

1. Fill and keep honest **`docs/lidb-capability-matrix.md`** (✅ only after harness green)
2. **Edit** lidb / lis (and opt-ins as needed) in sibling checkouts — not pin-tracking alone
3. Wire Librebase → `lis db start --profile librebase` (stub only via `LIDB_RUNTIME_MODE=dev`)
4. **Librebase Admin** (this repo): Studio UI + `admin-api/`
5. Opt-in packages: **li-oauth**, **li-edge**, **li-httpd**, **li-log** (Wave B+)
6. **`@librebase/librebase`** SDK + **`@librebase/cli`** / lip `librebase`
7. Tag **`v1.0.0` last** (after matrix rows are ✅ or honest ❌)

## Work packages (current sprint)

| WP | Deliverable | DoD |
|----|-------------|-----|
| WP-A | Capability matrix + this plan + SDD | Docs merged |
| WP-B | `admin-api/` inside librebase | Compose `librebase-admin` health; Studio client works |
| WP-C | Studio `/setup` + `/admin` | First-run + members/org view |
| WP-D | CLI lip + npm | `librebase --help` / `npx @librebase/cli --help` |
| WP-E | MCP server | Agent can health/setup/create-project/list + `parity_run` |
| WP-F | `profiles/librebase.toml` in **lis** | Documented; smoke with `LIDB_ROOT` |
| WP-G | Wave A harness | `scripts/parity_runner.py` skip/fail/pass honest (optional CI workflow needs `workflow` scope on push) |

## MCP testing model

Agents control the stack via **Librebase MCP** tools (`admin_*`, projects/instances, `matrix_status`, `parity_run`, `runtime_status`).

## What is *not* in Wave A

- Full GoTrue `/auth/v1` path alias
- S3 Storage API / Edge WASM runtime
- PITR / branching / Stripe billing
- Claiming matrix ✅ from emoji counts alone

## Success for “test with MCP”

```text
start admin-api → MCP admin_setup → create_project → list_projects → parity_run → matrix_status
```
