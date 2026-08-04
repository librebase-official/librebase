#!/usr/bin/env node
/**
 * Librebase MCP — agent control plane for Admin API + matrix docs.
 *
 * Cursor mcp.json example:
 * {
 *   "mcpServers": {
 *     "librebase": {
 *       "command": "node",
 *       "args": ["packages/mcp/src/server.js"],
 *       "env": { "LIBREBASE_ADMIN_URL": "http://127.0.0.1:54330" }
 *     }
 *   }
 * }
 */
import { readFileSync, existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { tools } from "./tools.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO =
  process.env.LIBREBASE_ROOT ??
  path.resolve(__dirname, "..", "..", "..");
const ADMIN_URL = (
  process.env.LIBREBASE_ADMIN_URL ?? "http://127.0.0.1:54330"
).replace(/\/$/, "");

function projectApiBase(override) {
  return (
    override ||
    process.env.LIBREBASE_PARITY_API ||
    process.env.LIBREBASE_PROJECT_API ||
    "http://127.0.0.1:54321"
  ).replace(/\/$/, "");
}

async function projectFetch(pathname, { apiBase, bearer, method = "GET", body } = {}) {
  const base = projectApiBase(apiBase);
  const headers = { "Content-Type": "application/json" };
  const token =
    bearer ||
    process.env.LIBREBASE_PROJECT_SESSION ||
    process.env.LIBREBASE_ADMIN_SESSION;
  if (token) headers.Authorization = `Bearer ${token}`;
  let res;
  try {
    res = await fetch(`${base}${pathname}`, {
      method,
      headers,
      body: body != null ? JSON.stringify(body) : undefined,
    });
  } catch (e) {
    return {
      ok: false,
      status: 0,
      body: { error: "unreachable", message: e instanceof Error ? e.message : String(e) },
    };
  }
  const text = await res.text();
  let json;
  try {
    json = JSON.parse(text);
  } catch {
    json = { raw: text };
  }
  return { ok: res.ok, status: res.status, body: json, apiBase: base };
}
function sessionHeaders() {
  const token =
    process.env.LIBREBASE_ADMIN_SESSION ?? process.env.LIBREBASE_ORG_SESSION;
  const h = { "Content-Type": "application/json" };
  if (token) h.Authorization = `Bearer ${token}`;
  return h;
}

async function adminFetch(pathname, init) {
  const res = await fetch(`${ADMIN_URL}${pathname}`, {
    ...init,
    headers: { ...sessionHeaders(), ...(init?.headers ?? {}) },
  });
  const text = await res.text();
  let json;
  try {
    json = JSON.parse(text);
  } catch {
    json = { raw: text };
  }
  return { ok: res.ok, status: res.status, body: json };
}

const server = new Server(
  { name: "librebase", version: "0.1.0" },
  { capabilities: { tools: {} } },
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({ tools }));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const name = request.params.name;
  const args = request.params.arguments ?? {};

  try {
    if (name === "admin_health") {
      const r = await adminFetch("/health");
      return { content: [{ type: "text", text: JSON.stringify(r, null, 2) }] };
    }
    if (name === "admin_setup") {
      const r = await adminFetch("/org/v1/setup", {
        method: "POST",
        body: JSON.stringify(args),
      });
      return { content: [{ type: "text", text: JSON.stringify(r, null, 2) }] };
    }
    if (name === "admin_login") {
      const r = await adminFetch("/org/v1/auth/login", {
        method: "POST",
        body: JSON.stringify(args),
      });
      return { content: [{ type: "text", text: JSON.stringify(r, null, 2) }] };
    }
    if (name === "list_projects") {
      const r = await adminFetch(`/org/v1/orgs/${args.orgId}/projects`);
      return { content: [{ type: "text", text: JSON.stringify(r, null, 2) }] };
    }
    if (name === "create_instance") {
      const r = await adminFetch(`/org/v1/orgs/${args.orgId}/instances`, {
        method: "POST",
        body: JSON.stringify({
          name: args.name,
          runtimeTarget: args.runtimeTarget ?? "local",
          ports: { api: 54320, postgres: 54322 },
        }),
      });
      return { content: [{ type: "text", text: JSON.stringify(r, null, 2) }] };
    }
    if (name === "create_project") {
      const r = await adminFetch(`/org/v1/orgs/${args.orgId}/projects`, {
        method: "POST",
        body: JSON.stringify({
          name: args.name,
          instanceId: args.instanceId,
          deploymentMode: args.deploymentMode ?? "dedicated",
          region: args.region ?? "local",
        }),
      });
      return { content: [{ type: "text", text: JSON.stringify(r, null, 2) }] };
    }
    if (name === "list_instances") {
      const r = await adminFetch(`/org/v1/orgs/${args.orgId}/instances`);
      return { content: [{ type: "text", text: JSON.stringify(r, null, 2) }] };
    }
    if (name === "studio_probe") {
      const url = (args.url ?? "http://127.0.0.1:3000").replace(/\/$/, "");
      try {
        const res = await fetch(url, { method: "GET" });
        const text = await res.text();
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(
                {
                  ok: res.ok,
                  status: res.status,
                  url,
                  bodyPreview: text.slice(0, 200),
                },
                null,
                2,
              ),
            },
          ],
        };
      } catch (e) {
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify({
                ok: false,
                url,
                error: e instanceof Error ? e.message : String(e),
              }),
            },
          ],
          isError: true,
        };
      }
    }
    if (name === "runtime_status") {
      const { spawnSync } = await import("node:child_process");
      const engine = path.join(REPO, "scripts", "lidb_engine.py");
      const python = process.env.PYTHON ?? "python";
      const result = spawnSync(
        python,
        [
          engine,
          "status",
          "--data-dir",
          String(args.dataDir),
          "--api-port",
          String(args.apiPort),
          "--postgres-port",
          String(args.postgresPort),
        ],
        { encoding: "utf8", cwd: REPO },
      );
      return {
        content: [
          {
            type: "text",
            text: result.stdout || result.stderr || `exit ${result.status}`,
          },
        ],
        isError: result.status !== 0,
      };
    }
    if (name === "parity_run") {
      const { spawnSync } = await import("node:child_process");
      const runner = path.join(REPO, "scripts", "parity_runner.py");
      const python = process.env.PYTHON ?? "python";
      const result = spawnSync(python, [runner], {
        encoding: "utf8",
        cwd: REPO,
        env: process.env,
      });
      return {
        content: [
          {
            type: "text",
            text: result.stdout || result.stderr || `exit ${result.status}`,
          },
        ],
        isError: result.status !== 0 && !String(result.stdout).includes('"status": "skipped"'),
      };
    }
    if (name === "check_entitlement") {
      const r = await adminFetch(
        `/org/v1/orgs/${args.orgId}/entitlements/${args.featureKey}`,
      );
      return { content: [{ type: "text", text: JSON.stringify(r, null, 2) }] };
    }
    if (name === "matrix_status") {
      const p = path.join(REPO, "docs", "lidb-capability-matrix.md");
      if (!existsSync(p)) {
        return {
          content: [{ type: "text", text: "matrix file missing" }],
          isError: true,
        };
      }
      const md = readFileSync(p, "utf8");
      const counts = { done: 0, wip: 0, todo: 0, skip: 0 };
      for (const line of md.split("\n")) {
        if (line.includes("| ✅ ")) counts.done += 1;
        else if (line.includes("| 🚧 ")) counts.wip += 1;
        else if (line.includes("| ⬜ ")) counts.todo += 1;
        else if (line.includes("| ❌ ")) counts.skip += 1;
      }
      const reportPath = path.join(REPO, "tests", "parity", "last-report.json");
      let harness = { status: "not_run" };
      if (existsSync(reportPath)) {
        try {
          harness = JSON.parse(readFileSync(reportPath, "utf8"));
        } catch {
          harness = { status: "invalid_report" };
        }
      }
      const pins = path.join(REPO, "docs", "li-dependency-pins.md");
      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(
              {
                path: p,
                counts,
                harness,
                pins: existsSync(pins) ? pins : null,
                ADMIN_URL,
              },
              null,
              2,
            ),
          },
        ],
      };
    }
    if (name === "execute_sql") {
      const r = await projectFetch("/rest/v1/rpc/exec", {
        apiBase: args.apiBase,
        bearer: args.bearer,
        method: "POST",
        body: { sql: args.sql },
      });
      // Prefer PostgREST-shaped; if 404 try thin /v1/sql
      let out = r;
      if (r.status === 404 || r.status === 0) {
        out = await projectFetch("/v1/sql", {
          apiBase: args.apiBase,
          bearer: args.bearer,
          method: "POST",
          body: { sql: args.sql },
        });
      }
      return {
        content: [{ type: "text", text: JSON.stringify(out, null, 2) }],
        isError: !out.ok || out.status === 0,
      };
    }
    if (name === "list_tables") {
      const schema = args.schema || "public";
      const r = await projectFetch(
        `/rest/v1/?select=*&limit=0`,
        { apiBase: args.apiBase, bearer: args.bearer },
      );
      // Honest: if OpenAPI root unavailable, return fail-closed probe
      if (!r.ok || r.status === 0) {
        const probe = await projectFetch(`/storage/v1`, {
          apiBase: args.apiBase,
          bearer: args.bearer,
        });
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(
                {
                  ok: false,
                  schema,
                  error: "list_tables_unavailable",
                  rest: r,
                  storage_probe: probe,
                  honesty: "Wire OpenAPI / information_schema when REST exposes it",
                },
                null,
                2,
              ),
            },
          ],
          isError: true,
        };
      }
      return { content: [{ type: "text", text: JSON.stringify(r, null, 2) }] };
    }
    if (name === "list_storage_buckets") {
      const r = await projectFetch("/storage/v1/bucket", {
        apiBase: args.apiBase,
        bearer: args.bearer,
      });
      return {
        content: [{ type: "text", text: JSON.stringify(r, null, 2) }],
        isError: !r.ok || r.status === 0,
      };
    }
    if (name === "list_edge_functions") {
      const r = await projectFetch("/functions/v1", {
        apiBase: args.apiBase,
        bearer: args.bearer,
      });
      return {
        content: [{ type: "text", text: JSON.stringify(r, null, 2) }],
        isError: r.status === 0,
      };
    }
    if (name === "get_auth_mfa_status") {
      const r = await projectFetch("/v1/auth/mfa", {
        apiBase: args.apiBase,
        bearer: args.bearer,
      });
      return {
        content: [{ type: "text", text: JSON.stringify(r, null, 2) }],
        isError: !r.ok || r.status === 0,
      };
    }
    if (name === "list_auth_users") {
      const q = new URLSearchParams();
      if (args.page != null) q.set("page", String(args.page));
      if (args.perPage != null) q.set("per_page", String(args.perPage));
      const qs = q.toString();
      const r = await projectFetch(`/auth/v1/admin/users${qs ? `?${qs}` : ""}`, {
        apiBase: args.apiBase,
        bearer: args.bearer,
      });
      return {
        content: [{ type: "text", text: JSON.stringify(r, null, 2) }],
        isError: !r.ok || r.status === 0,
      };
    }
    return {
      content: [{ type: "text", text: `Unknown tool: ${name}` }],
      isError: true,
    };
  } catch (e) {
    return {
      content: [
        {
          type: "text",
          text: e instanceof Error ? e.message : String(e),
        },
      ],
      isError: true,
    };
  }
});

const transport = new StdioServerTransport();
await server.connect(transport);
