/**
 * Todo-app E2E — spawns a lis backend + the todo-app HTTP server, then drives
 * the full public API surface over HTTP. Skips (exit 0) if lis is unavailable.
 */
import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const REPO = path.resolve(fileURLToPath(new URL("../../../", import.meta.url)));
const LIS_ROOT =
  process.env.LIS_ROOT ?? path.resolve(REPO, "..", "lis");
const API_PORT = 15432;
const APP_PORT = 18787;

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

async function waitHttp(url, retries = 60) {
  for (let i = 0; i < retries; i++) {
    try {
      const res = await fetch(url);
      if (res.ok || res.status < 500) return res;
    } catch {
      /* retry */
    }
    await sleep(250);
  }
  throw new Error(`never healthy: ${url}`);
}

async function run() {
  const tmp = mkdtempSync(path.join(tmpdir(), "todo-e2e-"));
  const children = [];
  const cleanup = () => children.forEach((c) => { try { c.kill("SIGKILL"); } catch {} });

  let lisProc;
  try {
    // 1. lis backend (mock auth, in-memory REST) on a random port
    lisProc = spawn(process.env.PYTHON ?? "python3", [
      path.join(LIS_ROOT, "routes", "registry", "server.py"),
      "--host", "127.0.0.1", "--port", String(API_PORT),
    ], {
      env: {
        ...process.env,
        PYTHONPATH: LIS_ROOT,
        LI_API_PORT: String(API_PORT),
        LI_JWT_SECRET: "e2e-secret-change-me",
        LI_AUTH_BACKEND: "mock",
        LI_REGISTRY_MOCK: "1",
        LI_DATA_DIR: path.join(tmp, "lis"),
      },
      stdio: ["ignore", "pipe", "pipe"],
    });
    lisProc.stderr.on("data", (d) => console.error("  [lis stderr]", d.toString().trim()));
    lisProc.stdout.on("data", (d) => console.error("  [lis stdout]", d.toString().trim()));
    lisProc.on("exit", (code) => console.error(`  [lis exited] code=${code}`));
    children.push(lisProc);
    await waitHttp(`http://127.0.0.1:${API_PORT}/rest/v1/todos?limit=1`);

    // 2. todo-app HTTP server
    const app = spawn(process.execPath, [path.join(REPO, "apps", "todo-app", "src", "server.mjs")], {
      env: {
        ...process.env,
        PORT: String(APP_PORT),
        LIBREBASE_API: `http://127.0.0.1:${API_PORT}`,
        LIBREBASE_ANON: "anon",
      },
      stdio: ["ignore", "pipe", "pipe"],
    });
    app.stderr.on("data", (d) => console.error("  [todo-app stderr]", d.toString().trim()));
    app.stdout.on("data", (d) => console.error("  [todo-app stdout]", d.toString().trim()));
    app.on("exit", (code) => console.error(`  [todo-app exited] code=${code}`));
    children.push(app);
    await waitHttp(`http://127.0.0.1:${APP_PORT}/health`);
  } catch (e) {
    cleanup();
    console.log(`todo-app e2e: SKIPPED (${e.message})`);
    return;
  }

  const BASE = `http://127.0.0.1:${APP_PORT}`;
  const EMAIL = `e2e-${Date.now()}@example.com`;
  const PASSWORD = "e2e-secret-change-me";

  // ---- UI served at / ----
  const index = await fetch(`${BASE}/`);
  assert.equal(index.status, 200, "GET / returns 200");
  const html = await index.text();
  assert.match(html, /Librebase Todo/, "root serves the todo UI");
  assert.match(html, /auth\/signup/, "UI references signup endpoint");

  // ---- health ----
  const health = await fetch(`${BASE}/health`);
  assert.equal(health.status, 200, "GET /health returns 200");
  const healthBody = await health.json();
  assert.equal(healthBody.service, "todo-app", "health names service");

  // ---- auth guard on todos ----
  const unauthTodos = await fetch(`${BASE}/todos`);
  assert.equal(unauthTodos.status, 401, "GET /todos without token is 401");

  // ---- signup returns a session token ----
  const signup = await fetch(`${BASE}/auth/signup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email: EMAIL, password: PASSWORD }),
  });
  assert.equal(signup.status, 201, "POST /auth/signup returns 201");
  const signupBody = await signup.json();
  assert.ok(signupBody.access_token, "signup returns access_token");
  assert.ok(signupBody.user?.id, "signup returns user");
  let token = signupBody.access_token;

  // ---- signin returns a token ----
  const signin = await fetch(`${BASE}/auth/signin`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email: EMAIL, password: PASSWORD }),
  });
  assert.equal(signin.status, 200, "POST /auth/signin returns 200");
  const signinBody = await signin.json();
  assert.ok(signinBody.access_token, "signin returns access_token");
  token = signinBody.access_token;

  // ---- todos CRUD with token ----
  const create = await fetch(`${BASE}/todos`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify({ title: "e2e todo" }),
  });
  assert.equal(create.status, 201, "POST /todos returns 201");
  const created = (await create.json()).todo;
  assert.ok(created.id, "created todo has id");
  assert.equal(created.title, "e2e todo", "created todo title");

  const list = await fetch(`${BASE}/todos`, { headers: { Authorization: `Bearer ${token}` } });
  assert.equal(list.status, 200, "GET /todos returns 200");
  const listBody = await list.json();
  assert.ok(Array.isArray(listBody.todos), "todos is an array");
  assert.ok(listBody.todos.some((t) => t.id === created.id), "created todo is listed");

  const complete = await fetch(`${BASE}/todos/${created.id}/complete`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  assert.equal(complete.status, 200, "complete returns 200");
  const completed = (await complete.json()).todo;
  assert.equal(completed.done, true, "todo marked done");

  // ---- delete ----
  const del = await fetch(`${BASE}/todos/${created.id}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
  assert.equal(del.status, 200, "DELETE returns 200");
  const after = await fetch(`${BASE}/todos`, { headers: { Authorization: `Bearer ${token}` } });
  const afterBody = await after.json();
  assert.ok(!afterBody.todos.some((t) => t.id === created.id), "todo deleted");

  // ---- bad password rejected ----
  const bad = await fetch(`${BASE}/auth/signin`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email: EMAIL, password: "wrong-password" }),
  });
  assert.equal(bad.status, 401, "wrong password is 401");

  cleanup();
  console.log("todo-app e2e ok: UI + health + signup(token) + signin + todos CRUD + auth guards");
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  run().then(() => process.exit(0)).catch((e) => { console.error(e); process.exit(1); });
}
