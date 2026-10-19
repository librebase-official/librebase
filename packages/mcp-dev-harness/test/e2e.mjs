import { spawn } from "node:child_process";
import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const REPO = path.resolve(fileURLToPath(new URL("../", import.meta.url)), "..", "..");
const ADMIN_PORT = 54345;
const tmp = mkdtempSync(path.join(tmpdir(), "mcp-e2e-"));

const admin = spawn(
  process.env.PYTHON ?? "python3",
  ["admin-api/scripts/admin_server.py"],
  {
    env: {
      ...process.env,
      LIBREBASE_ADMIN_BIND: "127.0.0.1",
      LIBREBASE_ADMIN_PORT: String(ADMIN_PORT),
      LIBREBASE_ADMIN_DB_PATH: path.join(tmp, "e2e.db"),
      LIBREBASE_ADMIN_JWT_SECRET: "mcp-e2e-secret",
    },
    cwd: REPO,
    stdio: "ignore",
  },
);

async function waitHealthy(retries = 50) {
  for (let i = 0; i < retries; i++) {
    try {
      const res = await fetch(`http://127.0.0.1:${ADMIN_PORT}/health`);
      if (res.ok) return;
    } catch {
      /* retry */
    }
    await new Promise((r) => setTimeout(r, 200));
  }
  throw new Error("admin never became healthy");
}
await waitHealthy();

const SERVER = new URL("../src/server.js", import.meta.url);
const child = spawn("node", [SERVER.pathname], {
  env: {
    ...process.env,
    LIBREBASE_ADMIN_URL: `http://127.0.0.1:${ADMIN_PORT}`,
  },
  stdio: ["pipe", "pipe", "inherit"],
});

const pending = new Map();
let buffer = "";
let nextId = 1;

child.stdout.on("data", (chunk) => {
  buffer += chunk.toString();
  let idx;
  while ((idx = buffer.indexOf("\n")) !== -1) {
    const line = buffer.slice(0, idx).trim();
    buffer = buffer.slice(idx + 1);
    if (!line) continue;
    let msg;
    try {
      msg = JSON.parse(line);
    } catch {
      continue;
    }
    const waiter = pending.get(msg.id);
    if (waiter) {
      pending.delete(msg.id);
      waiter(msg);
    }
  }
});

function send(method, params) {
  return new Promise((resolve, reject) => {
    const id = String(nextId++);
    pending.set(id, resolve);
    child.stdin.write(
      JSON.stringify({ jsonrpc: "2.0", id, method, params }) + "\n",
      (err) => err && reject(err),
    );
  });
}

async function call(name, args = {}) {
  const res = await send("tools/call", { name, arguments: args });
  const text = res.result?.content?.[0]?.text;
  return JSON.parse(text);
}

await send("initialize", {
  protocolVersion: "2024-11-05",
  capabilities: {},
  clientInfo: { name: "smoke", version: "0" },
});
child.stdin.write(
  JSON.stringify({ jsonrpc: "2.0", method: "notifications/initialized" }) + "\n",
);

let setup = await call("admin_setup", { name: "MCP Org", ownerEmail: "mcp@localhost", password: "secret" });
if (!setup.ok && setup.status === 409) {
  setup = await call("admin_login", { email: "mcp@localhost", password: "secret" });
}
if (!setup.ok) throw new Error(`setup/login failed: ${JSON.stringify(setup)}`);

const status = await call("auth_status");
if (!status.adminAuthenticated) throw new Error("expected adminAuthenticated after setup");

const host = await call("create_host", { name: "mcp-vm", memMb: 512 });
if (!host.ok) throw new Error(`create_host failed: ${JSON.stringify(host)}`);
const hostId = host.body.id;

const inst = await call("create_instance", { name: "mcp-inst", hostId, memLimitMb: 256 });
if (!inst.ok || inst.body.hostId !== hostId) throw new Error(`create_instance failed: ${JSON.stringify(inst)}`);

const listHosts = await call("list_hosts");
if (!Array.isArray(listHosts.body)) throw new Error(`list_hosts failed: ${JSON.stringify(listHosts)}`);

const listInsts = await call("list_instances");
if (!Array.isArray(listInsts.body)) throw new Error(`list_instances failed: ${JSON.stringify(listInsts)}`);

const over = await call("create_instance", { name: "over", hostId, memLimitMb: 400 });
if (over.status !== 409) throw new Error(`expected budget 409 got ${over.status}`);

const logout = await call("admin_logout");
const statusAfter = await call("auth_status");
if (statusAfter.adminAuthenticated) throw new Error("expected adminAuthenticated=false after logout");

console.log("mcp e2e ok: setup->auth->host->instance->list->budget409->logout");
child.kill();
admin.kill();
process.exit(0);
