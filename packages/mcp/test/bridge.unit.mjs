/**
 * Hosted MCP bridge unit tests (mock HTTP server).
 */
import assert from "node:assert/strict";
import http from "node:http";
import { createHostedBridge, DEFAULT_MCP_URL } from "../src/bridge.js";

function startMockHosted(handler) {
  return new Promise((resolve) => {
    const server = http.createServer((req, res) => {
      if (req.method !== "POST") {
        res.writeHead(405);
        res.end();
        return;
      }
      let raw = "";
      req.on("data", (c) => {
        raw += c;
      });
      req.on("end", () => {
        const msg = JSON.parse(raw);
        handler(req, res, msg);
      });
    });
    server.listen(0, "127.0.0.1", () => {
      const { port } = server.address();
      resolve({
        url: `http://127.0.0.1:${port}/api/mcp`,
        close: () =>
          new Promise((r) => server.close(() => r())),
      });
    });
  });
}

const sampleTools = [
  {
    name: "auth_start",
    description: "device",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "org_whoami",
    description: "who",
    inputSchema: { type: "object", properties: {} },
  },
];

async function testListAndForward() {
  const mock = await startMockHosted((req, res, msg) => {
    if (msg.method === "tools/list") {
      assert.equal(req.headers.authorization, undefined);
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(
        JSON.stringify({
          jsonrpc: "2.0",
          id: msg.id,
          result: { tools: sampleTools },
        }),
      );
      return;
    }
    assert.equal(msg.method, "tools/call");
    assert.equal(msg.params.name, "org_whoami");
    assert.match(req.headers.authorization ?? "", /^Bearer tok-env$/);
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(
      JSON.stringify({
        jsonrpc: "2.0",
        id: msg.id,
        result: { content: [{ type: "text", text: '{"orgId":"o1"}' }] },
      }),
    );
  });

  const bridge = createHostedBridge({
    url: mock.url,
    token: "tok-env",
    fetch: globalThis.fetch,
  });
  const tools = await bridge.listTools();
  assert.equal(tools.length, 2);
  assert.equal(tools[0].name, "auth_start");

  const out = await bridge.callTool("org_whoami", {});
  assert.match(out.content[0].text, /o1/);

  await mock.close();
}

async function testDeviceFlowNoBearerOnPublicTools() {
  const mock = await startMockHosted((req, res, msg) => {
    if (msg.method === "tools/call" && msg.params.name === "auth_start") {
      assert.equal(req.headers.authorization, undefined);
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(
        JSON.stringify({
          jsonrpc: "2.0",
          id: msg.id,
          result: {
            content: [
              {
                type: "text",
                text: JSON.stringify({ deviceCode: "dc", verificationUri: "https://x" }),
              },
            ],
          },
        }),
      );
      return;
    }
    if (msg.method === "tools/call" && msg.params.name === "auth_poll") {
      assert.equal(req.headers.authorization, undefined);
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(
        JSON.stringify({
          jsonrpc: "2.0",
          id: msg.id,
          result: {
            content: [
              {
                type: "text",
                text: JSON.stringify({ accessToken: "lb_agt_secret", status: "approved" }),
              },
            ],
          },
        }),
      );
      return;
    }
    res.writeHead(400);
    res.end();
  });

  const bridge = createHostedBridge({ url: mock.url, fetch: globalThis.fetch });
  await bridge.callTool("auth_start", { clientName: "test" });
  await bridge.callTool("auth_poll", { deviceCode: "dc" });
  assert.equal(bridge.getSessionToken(), "lb_agt_secret");

  const protectedMock = await startMockHosted((req, res, msg) => {
    assert.match(req.headers.authorization ?? "", /^Bearer lb_agt_secret$/);
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(
      JSON.stringify({
        jsonrpc: "2.0",
        id: msg.id,
        result: { content: [{ type: "text", text: "{}" }] },
      }),
    );
  });
  bridge.setMcpUrl(protectedMock.url);
  await bridge.callTool("org_whoami", {});
  await protectedMock.close();
  await mock.close();
}

async function testEndpointOverride() {
  const mock = await startMockHosted((req, res, msg) => {
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(
      JSON.stringify({
        jsonrpc: "2.0",
        id: msg.id,
        result: { tools: [] },
      }),
    );
  });
  const bridge = createHostedBridge({ url: mock.url, fetch: globalThis.fetch });
  assert.equal(bridge.getMcpUrl(), mock.url);
  assert.notEqual(bridge.getMcpUrl(), DEFAULT_MCP_URL);
  await bridge.listTools();
  await mock.close();
}

await testListAndForward();
await testDeviceFlowNoBearerOnPublicTools();
await testEndpointOverride();

console.log("mcp bridge unit ok");
