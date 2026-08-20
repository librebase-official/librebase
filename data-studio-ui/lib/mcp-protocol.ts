/**
 * MCP JSON-RPC over HTTP. Tools proxy to the admin API with the caller's
 * MCP key (lb_mcp_…) as Bearer. No PYTHONPATH, no local stdio.
 */

export const MCP_PROTOCOL_VERSION = "2024-11-05";

export const MCP_TOOLS = [
  {
    name: "org_whoami",
    description: "Resolve the MCP key's org (id, name, edition).",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "project_list",
    description: "List projects in the org.",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "project_get",
    description: "Get one project by id.",
    inputSchema: {
      type: "object",
      required: ["projectId"],
      properties: { projectId: { type: "string" } },
    },
  },
  {
    name: "project_create",
    description: "Create a project (requires an existing instanceId).",
    inputSchema: {
      type: "object",
      required: ["name", "instanceId"],
      properties: {
        name: { type: "string" },
        instanceId: { type: "string" },
        region: { type: "string" },
        deploymentMode: { type: "string", enum: ["dedicated", "shared"] },
      },
    },
  },
  {
    name: "instance_list",
    description: "List instances in the org.",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "instance_get",
    description: "Get one instance by id.",
    inputSchema: {
      type: "object",
      required: ["instanceId"],
      properties: { instanceId: { type: "string" } },
    },
  },
  {
    name: "member_list",
    description: "List org members.",
    inputSchema: { type: "object", properties: {} },
  },
] as const;

type Json = Record<string, unknown>;

export interface JsonRpcRequest {
  jsonrpc?: string;
  id?: string | number | null;
  method?: string;
  params?: { name?: string; arguments?: Json };
}

export interface JsonRpcResponse {
  jsonrpc: "2.0";
  id: string | number | null;
  result?: unknown;
  error?: { code: number; message: string };
}

function oneLineError(status: number, body: unknown): string {
  if (body && typeof body === "object" && "error" in body) {
    return String((body as { error: unknown }).error);
  }
  if (status === 401) return "Invalid MCP key — generate a new one on the project Connect panel.";
  if (status === 403) return "This key cannot access that org.";
  if (status === 404) return "Not found — check the project or instance id.";
  return `Admin API ${status}`;
}

async function adminCall(
  adminUrl: string,
  mcpKey: string,
  method: string,
  path: string,
  body?: Json,
): Promise<{ ok: boolean; status: number; payload: unknown }> {
  const res = await fetch(`${adminUrl.replace(/\/$/, "")}${path}`, {
    method,
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      Authorization: `Bearer ${mcpKey}`,
    },
    body: body ? JSON.stringify(body) : undefined,
    cache: "no-store",
  });
  const text = await res.text();
  let payload: unknown = text;
  try {
    payload = text ? JSON.parse(text) : {};
  } catch {
    payload = { error: text || `http ${res.status}` };
  }
  return { ok: res.ok, status: res.status, payload };
}

export async function handleMcpRpc(
  msg: JsonRpcRequest,
  opts: { adminUrl: string; mcpKey: string },
): Promise<JsonRpcResponse | null> {
  const id = msg.id ?? null;
  const method = msg.method ?? "";

  if (method === "notifications/initialized" || method.startsWith("notifications/")) {
    return null;
  }

  if (method === "initialize") {
    return {
      jsonrpc: "2.0",
      id,
      result: {
        protocolVersion: MCP_PROTOCOL_VERSION,
        capabilities: { tools: {} },
        serverInfo: { name: "librebase", version: "0.2.0" },
      },
    };
  }

  if (method === "tools/list" || method === "tools/listChanged") {
    return { jsonrpc: "2.0", id, result: { tools: MCP_TOOLS } };
  }

  if (method === "ping") {
    return { jsonrpc: "2.0", id, result: {} };
  }

  if (method !== "tools/call") {
    return {
      jsonrpc: "2.0",
      id,
      error: { code: -32601, message: `method not found: ${method}` },
    };
  }

  const tool = String(msg.params?.name ?? "");
  const args = { ...(msg.params?.arguments ?? {}) };
  let payload: unknown;
  try {
    payload = await callTool(tool, args, opts);
  } catch (e) {
    payload = { error: e instanceof Error ? e.message : "tool_error" };
  }

  return {
    jsonrpc: "2.0",
    id,
    result: {
      content: [{ type: "text", text: JSON.stringify(payload, null, 2) }],
      isError: Boolean(
        payload && typeof payload === "object" && "error" in (payload as Json),
      ),
    },
  };
}

async function callTool(
  name: string,
  args: Json,
  opts: { adminUrl: string; mcpKey: string },
): Promise<unknown> {
  const orgRes = await adminCall(opts.adminUrl, opts.mcpKey, "GET", "/org/v1/mcp/org");
  if (!orgRes.ok) {
    return { error: oneLineError(orgRes.status, orgRes.payload) };
  }
  const orgId = String((orgRes.payload as Json)?.orgId ?? "");
  if (!orgId) return { error: "could not resolve org from MCP key" };

  const get = (path: string) => adminCall(opts.adminUrl, opts.mcpKey, "GET", path);
  const post = (path: string, body: Json) =>
    adminCall(opts.adminUrl, opts.mcpKey, "POST", path, body);

  let res: { ok: boolean; status: number; payload: unknown };
  if (name === "org_whoami") {
    res = orgRes;
  } else if (name === "project_list") {
    res = await get(`/org/v1/orgs/${orgId}/projects`);
  } else if (name === "project_get") {
    const projectId = String(args.projectId ?? "");
    if (!projectId) return { error: "projectId is required" };
    res = await get(`/org/v1/orgs/${orgId}/projects/${projectId}`);
  } else if (name === "project_create") {
    res = await post(`/org/v1/orgs/${orgId}/projects`, args);
  } else if (name === "instance_list") {
    res = await get(`/org/v1/orgs/${orgId}/instances`);
  } else if (name === "instance_get") {
    const instanceId = String(args.instanceId ?? "");
    if (!instanceId) return { error: "instanceId is required" };
    res = await get(`/org/v1/orgs/${orgId}/instances/${instanceId}`);
  } else if (name === "member_list") {
    res = await get(`/org/v1/orgs/${orgId}/members`);
  } else {
    return { error: `unknown tool ${name}` };
  }

  if (!res.ok) return { error: oneLineError(res.status, res.payload) };
  return res.payload;
}

export function extractMcpKey(request: Request): string | null {
  const auth = request.headers.get("authorization") ?? "";
  if (auth.toLowerCase().startsWith("bearer ")) {
    const token = auth.slice(7).trim();
    return token || null;
  }
  const headerKey = request.headers.get("x-librebase-mcp-key")?.trim();
  return headerKey || null;
}
