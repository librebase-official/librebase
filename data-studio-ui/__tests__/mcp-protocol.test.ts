import { describe, expect, it } from "vitest";
import {
  extractMcpKey,
  handleMcpRpc,
  MCP_TOOLS,
} from "@/lib/mcp-protocol";

describe("mcp-protocol", () => {
  it("extracts bearer keys", () => {
    const req = new Request("https://app.librebase.xyz/mcp", {
      headers: { Authorization: "Bearer lb_mcp_abc" },
    });
    expect(extractMcpKey(req)).toBe("lb_mcp_abc");
  });

  it("initialize and tools/list do not need the admin API", async () => {
    const init = await handleMcpRpc(
      { jsonrpc: "2.0", id: 1, method: "initialize" },
      { adminUrl: "http://127.0.0.1:9", mcpKey: "x" },
    );
    expect(init?.result).toMatchObject({
      protocolVersion: "2024-11-05",
      serverInfo: { name: "librebase" },
    });

    const listed = await handleMcpRpc(
      { jsonrpc: "2.0", id: 2, method: "tools/list" },
      { adminUrl: "http://127.0.0.1:9", mcpKey: "x" },
    );
    const tools = (listed?.result as { tools: { name: string }[] }).tools;
    expect(tools.map((t) => t.name)).toEqual(
      expect.arrayContaining(["org_whoami", "project_list", "project_get"]),
    );
    expect(MCP_TOOLS.length).toBeGreaterThan(3);
  });

  it("unknown methods return JSON-RPC -32601", async () => {
    const res = await handleMcpRpc(
      { jsonrpc: "2.0", id: 3, method: "nope" },
      { adminUrl: "http://127.0.0.1:9", mcpKey: "x" },
    );
    expect(res?.error?.code).toBe(-32601);
  });
});
