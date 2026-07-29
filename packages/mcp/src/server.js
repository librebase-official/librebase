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

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO =
  process.env.LIBREBASE_ROOT ??
  path.resolve(__dirname, "..", "..", "..");
const ADMIN_URL = (
  process.env.LIBREBASE_ADMIN_URL ?? "http://127.0.0.1:54330"
).replace(/\/$/, "");

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

const tools = [
  {
    name: "admin_health",
    description: "GET Librebase Admin API /health",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "admin_setup",
    description: "First-run POST /org/v1/setup (creates org + owner + JWT)",
    inputSchema: {
      type: "object",
      properties: {
        name: { type: "string" },
        ownerEmail: { type: "string" },
        password: { type: "string" },
      },
      required: ["name", "ownerEmail", "password"],
    },
  },
  {
    name: "admin_login",
    description: "POST /org/v1/auth/login → session JWT",
    inputSchema: {
      type: "object",
      properties: {
        email: { type: "string" },
        password: { type: "string" },
      },
      required: ["email", "password"],
    },
  },
  {
    name: "list_projects",
    description: "GET /org/v1/orgs/{orgId}/projects",
    inputSchema: {
      type: "object",
      properties: { orgId: { type: "string" } },
      required: ["orgId"],
    },
  },
  {
    name: "create_instance",
    description: "POST /org/v1/orgs/{orgId}/instances",
    inputSchema: {
      type: "object",
      properties: {
        orgId: { type: "string" },
        name: { type: "string" },
        runtimeTarget: { type: "string" },
      },
      required: ["orgId", "name"],
    },
  },
  {
    name: "create_project",
    description: "POST /org/v1/orgs/{orgId}/projects (needs instanceId)",
    inputSchema: {
      type: "object",
      properties: {
        orgId: { type: "string" },
        name: { type: "string" },
        instanceId: { type: "string" },
        deploymentMode: { type: "string" },
        region: { type: "string" },
      },
      required: ["orgId", "name", "instanceId"],
    },
  },
  {
    name: "list_instances",
    description: "GET /org/v1/orgs/{orgId}/instances",
    inputSchema: {
      type: "object",
      properties: { orgId: { type: "string" } },
      required: ["orgId"],
    },
  },
  {
    name: "studio_probe",
    description: "GET a Studio URL (default http://127.0.0.1:3000) for liveness",
    inputSchema: {
      type: "object",
      properties: {
        url: { type: "string" },
      },
    },
  },
  {
    name: "runtime_status",
    description: "Run scripts/lidb_engine.py status when data-dir/ports provided",
    inputSchema: {
      type: "object",
      properties: {
        dataDir: { type: "string" },
        apiPort: { type: "number" },
        postgresPort: { type: "number" },
      },
      required: ["dataDir", "apiPort", "postgresPort"],
    },
  },
  {
    name: "parity_run",
    description: "Run Wave A scripts/parity_runner.py; returns JSON report",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "check_entitlement",
    description: "GET entitlement flag for org",
    inputSchema: {
      type: "object",
      properties: {
        orgId: { type: "string" },
        featureKey: { type: "string" },
      },
      required: ["orgId", "featureKey"],
    },
  },
  {
    name: "matrix_status",
    description: "Summarize capability matrix + last parity harness report",
    inputSchema: { type: "object", properties: {} },
  },
];

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
