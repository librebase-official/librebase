/**
 * Thin stdio → hosted MCP bridge (no local tool catalog).
 */
import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export const DEFAULT_MCP_URL = "https://app.librebase.xyz/api/mcp";

const PUBLIC_TOOL_CALLS = new Set(["auth_start", "auth_poll"]);
const PUBLIC_METHODS = new Set([
  "initialize",
  "notifications/initialized",
  "tools/list",
]);

export function readPackageVersion() {
  try {
    const pkg = JSON.parse(
      readFileSync(path.join(__dirname, "..", "package.json"), "utf8"),
    );
    return pkg.version ?? "0.0.0";
  } catch {
    return "0.0.0";
  }
}

export function createHostedBridge(options = {}) {
  const fetchImpl = options.fetch ?? globalThis.fetch;
  let mcpUrl = (options.url ?? process.env.LIBREBASE_MCP_URL ?? DEFAULT_MCP_URL).replace(
    /\/$/,
    "",
  );
  let sessionToken = (options.token ?? process.env.LIBREBASE_MCP_TOKEN ?? "").trim();

  function setMcpUrl(url) {
    mcpUrl = String(url).replace(/\/$/, "");
  }

  function getSessionToken() {
    return sessionToken;
  }

  function setSessionToken(token) {
    sessionToken = String(token ?? "").trim();
  }

  function authHeaderForMessage(method, params) {
    const toolName =
      method === "tools/call" ? String(params?.name ?? "") : "";
    const isPublic =
      PUBLIC_METHODS.has(method) ||
      (method === "tools/call" && PUBLIC_TOOL_CALLS.has(toolName));
    if (isPublic || !sessionToken) return {};
    return { Authorization: `Bearer ${sessionToken}` };
  }

  function tryCaptureTokenFromToolResult(result, toolName) {
    if (toolName !== "auth_poll" || !result?.content?.[0]?.text) return;
    try {
      const payload = JSON.parse(result.content[0].text);
      if (typeof payload.accessToken === "string" && payload.accessToken) {
        sessionToken = payload.accessToken;
      }
    } catch {
      /* ignore malformed poll payloads */
    }
  }

  async function hostedJsonRpc(method, params, id) {
    const body = { jsonrpc: "2.0", method, params: params ?? {}, id };
    const headers = {
      "Content-Type": "application/json",
      Accept: "application/json",
      ...authHeaderForMessage(method, params),
    };
    let res;
    try {
      res = await fetchImpl(mcpUrl, {
        method: "POST",
        headers,
        body: JSON.stringify(body),
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      return {
        jsonrpc: "2.0",
        id,
        error: { code: -32000, message: `hosted_unreachable: ${message}` },
      };
    }

    if (res.status === 204) {
      return null;
    }

    const text = await res.text();
    if (!text) {
      return {
        jsonrpc: "2.0",
        id,
        error: {
          code: -32000,
          message: `hosted_empty_response (${res.status})`,
        },
      };
    }

    let msg;
    try {
      msg = JSON.parse(text);
    } catch {
      return {
        jsonrpc: "2.0",
        id,
        error: {
          code: -32000,
          message: `hosted_invalid_json (${res.status})`,
        },
      };
    }

    if (!res.ok && msg.error == null) {
      return {
        jsonrpc: "2.0",
        id,
        error: {
          code: -32000,
          message:
            typeof msg.error === "string"
              ? msg.error
              : `hosted_http_${res.status}`,
        },
      };
    }

    if (method === "tools/call" && msg.result) {
      tryCaptureTokenFromToolResult(msg.result, String(params?.name ?? ""));
    }

    return msg;
  }

  async function listTools() {
    const res = await hostedJsonRpc("tools/list", {}, "bridge-list-tools");
    if (res.error) {
      throw new Error(res.error.message ?? "tools/list failed");
    }
    return res.result?.tools ?? [];
  }

  async function callTool(name, args) {
    const res = await hostedJsonRpc(
      "tools/call",
      { name, arguments: args ?? {} },
      `bridge-call-${name}`,
    );
    if (res.error) {
      throw new Error(res.error.message ?? `tools/call ${name} failed`);
    }
    return res.result;
  }

  function localInitialize(id) {
    return {
      jsonrpc: "2.0",
      id,
      result: {
        protocolVersion: "2024-11-05",
        capabilities: { tools: {} },
        serverInfo: {
          name: "librebase-mcp-bridge",
          version: readPackageVersion(),
        },
      },
    };
  }

  return {
    getMcpUrl: () => mcpUrl,
    setMcpUrl,
    getSessionToken,
    setSessionToken,
    hostedJsonRpc,
    listTools,
    callTool,
    localInitialize,
  };
}
