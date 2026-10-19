#!/usr/bin/env node
/**
 * Librebase MCP — stdio bridge to hosted Streamable HTTP MCP.
 *
 * Env:
 *   LIBREBASE_MCP_URL   — default https://app.librebase.xyz/api/mcp
 *   LIBREBASE_MCP_TOKEN — optional lb_mcp_* / lb_agt_* bearer (never logged)
 *   LIBREBASE_MCP_KEY   — deprecated alias for LIBREBASE_MCP_TOKEN
 */
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { createHostedBridge, readPackageVersion } from "./bridge.js";

const bridge = createHostedBridge();

const server = new Server(
  { name: "librebase-mcp-bridge", version: readPackageVersion() },
  { capabilities: { tools: {} } },
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: await bridge.listTools(),
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const name = request.params.name;
  const args = request.params.arguments ?? {};
  try {
    const result = await bridge.callTool(name, args);
    return result;
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
