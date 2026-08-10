/**
 * Supabase todo-app unit tests — offline via mock fetch.
 */
import assert from "node:assert/strict";
import { fileURLToPath } from "node:url";
import { createSupabaseTodoApp } from "../src/app.mjs";

function mockFetch(routes) {
  const calls = [];
  const impl = async (input, init = {}) => {
    const url = String(input);
    const method = init.method ?? "GET";
    calls.push({ url, method });
    for (const [matcher, responder] of routes) {
      if (matcher(url, method)) {
        const r = await responder({ url, method, init });
        return new Response(JSON.stringify(r.body), { status: r.status, headers: { "Content-Type": "application/json" } });
      }
    }
    return new Response(JSON.stringify({ message: "unhandled" }), { status: 404, headers: { "Content-Type": "application/json" } });
  };
  return { calls, impl };
}

export async function run() {
  const store = { todos: [] };
  const fakeJwt = () => `header.${Buffer.from(JSON.stringify({ sub: "u-1" })).toString("base64url")}.sig`;
  const routes = [
    [(u, m) => u.includes("/auth/v1/signup") && m === "POST", async () => ({ status: 200, body: { user: { id: "u-1", email: "a@b.c" }, access_token: fakeJwt(), refresh_token: "rt" } })],
    [(u, m) => u.includes("/auth/v1/token") && m === "POST", async () => ({ status: 200, body: { access_token: fakeJwt(), refresh_token: "rt", user: { id: "u-1" } } })],
    [(u, m) => u.includes("/rest/v1/todos") && m === "POST", async ({ init }) => {
      const row = { id: `t-${store.todos.length + 1}`, ...JSON.parse(init.body), done: false };
      store.todos.push(row);
      return { status: 201, body: [row] };
    }],
    [(u, m) => u.includes("/rest/v1/todos") && m === "GET", async () => ({ status: 200, body: store.todos })],
    [(u, m) => u.includes("/rest/v1/todos/") && m === "PATCH", async ({ url, init }) => {
      const id = url.split("/rest/v1/todos/")[1].split("?")[0];
      const row = store.todos.find((t) => t.id === id);
      Object.assign(row, JSON.parse(init.body));
      return { status: 200, body: [row] };
    }],
    [(u, m) => u.includes("/rest/v1/todos/") && m === "DELETE", async () => ({ status: 200, body: { deleted: true } })],
  ];
  const { calls, impl } = mockFetch(routes);
  const app = createSupabaseTodoApp("https://x.supabase.co", "anon", { fetch: impl });

  const up = await app.auth.signUp("a@b.c", "pw");
  assert.ok(up.user?.id, "signup returns user");
  const inn = await app.auth.signIn("a@b.c", "pw");
  assert.ok(inn.session?.access_token, "signin returns session");

  const created = await app.todos.create("unit", "u-1");
  assert.equal(created.title, "unit");
  assert.equal(created.done, false);
  const list = await app.todos.list();
  assert.equal(list.length, 1);
  const done = await app.todos.complete(created.id);
  assert.equal(done.done, true);
  await app.todos.remove(created.id);

  // create requires title + userId (RLS)
  let threw = false;
  try { await app.todos.create("   ", "u-1"); } catch { threw = true; }
  assert.ok(threw, "blank title rejected");

  console.log("supabase todo-app unit ok");
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  run().then(() => process.exit(0)).catch((e) => { console.error(e); process.exit(1); });
}
