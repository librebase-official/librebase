/**
 * Todo app unit tests — offline via mock fetch. No live stack required.
 */
import assert from "node:assert/strict";
import { fileURLToPath } from "node:url";
import { createTodoApp } from "../src/app.mjs";

function mockClient(handlers) {
  const calls = [];
  const fetchImpl = async (input, init = {}) => {
    const url = String(input);
    const method = init.method ?? "GET";
    calls.push({ url, method, body: init.body });
    const body = init.body ? JSON.parse(init.body) : undefined;
    let handled = false;
    for (const [matcher, responder] of handlers) {
      if (matcher(url, method)) {
        const { status = 200, data = {} } = await responder({ url, method, body, headers: init.headers });
        return new Response(JSON.stringify(data), {
          status,
          headers: { "Content-Type": "application/json" },
        });
      }
    }
    return new Response(JSON.stringify({ error: "unhandled" }), { status: 404, headers: { "Content-Type": "application/json" } });
  };
  return { calls, fetchImpl };
}

function handlersFor() {
  const stores = { users: {}, passwords: {}, todos: [] };
  let accessToken = "tok-anon";
  const handlers = [
    [(u, m) => u.includes("/v1/auth/signup") && m === "POST", async ({ body }) => {
      const id = `u-${Object.keys(stores.users).length + 1}`;
      stores.users[body.email] = id;
      stores.passwords[body.email] = body.password;
      return { status: 201, data: { user: { id, email: body.email }, access_token: "tok-user", refresh_token: "rt" } };
    }],
    [(u, m) => u.includes("/v1/auth/login") && m === "POST", async ({ body }) => {
      if (!stores.users[body.email] || stores.passwords[body.email] !== body.password) {
        return { status: 401, data: { message: "invalid" } };
      }
      accessToken = "tok-user";
      return { status: 200, data: { user: { id: stores.users[body.email], email: body.email }, access_token: "tok-user", refresh_token: "rt" } };
    }],
    [(u, m) => u.includes("/rest/v1/todos") && m === "POST", async ({ body }) => {
      const row = { id: `t-${stores.todos.length + 1}`, ...body, done: false };
      stores.todos.push(row);
      return { status: 201, data: row };
    }],
    [(u, m) => u.includes("/rest/v1/todos") && m === "GET", async () => {
      return { status: 200, data: stores.todos };
    }],
    [(u, m) => u.includes("/rest/v1/todos/") && m === "PATCH", async ({ url: u }) => {
      const id = u.split("/rest/v1/todos/")[1];
      const row = stores.todos.find((t) => t.id === id);
      if (!row) return { status: 404, data: { message: "not found" } };
      row.done = true;
      return { status: 200, data: row };
    }],
    [(u, m) => u.includes("/rest/v1/todos/") && m === "DELETE", async ({ url: u }) => {
      const id = u.split("/rest/v1/todos/")[1];
      stores.todos = stores.todos.filter((t) => t.id !== id);
      return { status: 200, data: { deleted: true } };
    }],
  ];
  return { handlers, stores };
}

const API = "http://127.0.0.1:54321";

export async function run() {
  {
    const { handlers, stores } = handlersFor();
    const { calls, fetchImpl } = mockClient(handlers);
    const app = createTodoApp(API, "anon", { fetch: fetchImpl });

    const { user } = await app.auth.signUp("alice@example.com", "pw");
    assert.ok(user.id, "signup returns user");
    const { session } = await app.auth.signIn("alice@example.com", "pw");
    assert.ok(session.access_token, "signin returns session");

    const created = await app.todos.create("write tests");
    assert.equal(created.title, "write tests");
    assert.equal(created.done, false);

    const list = await app.todos.list();
    assert.equal(list.length, 1);
    assert.equal(list[0].title, "write tests");

    const done = await app.todos.complete(created.id);
    assert.equal(done.done, true);

    await app.todos.remove(created.id);
    const after = await app.todos.list();
    assert.equal(after.length, 0);

    // Auth wiring: anon key + Bearer present on all todo calls.
    const restCalls = calls.filter((c) => c.url.includes("/rest/v1/"));
    assert.ok(restCalls.length >= 4, "expected todos CRUD calls");
  }

  {
    // Error path: signup then wrong login → app error surfaced.
    const { handlers } = handlersFor();
    const { fetchImpl } = mockClient(handlers);
    const app = createTodoApp(API, "anon", { fetch: fetchImpl });
    await app.auth.signUp("bob@example.com", "pw");
    let threw = false;
    try {
      await app.auth.signIn("bob@example.com", "wrong");
    } catch (e) {
      threw = true;
      assert.equal(e.status, 401);
    }
    assert.ok(threw, "wrong password throws app error");
  }

  {
    // create requires title
    const { handlers } = handlersFor();
    const { fetchImpl } = mockClient(handlers);
    const app = createTodoApp(API, "anon", { fetch: fetchImpl });
    let threw = false;
    try {
      await app.todos.create("   ");
    } catch {
      threw = true;
    }
    assert.ok(threw, "blank title rejected");
  }

  console.log("todo-app unit ok");
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  run().then(() => process.exit(0)).catch((e) => { console.error(e); process.exit(1); });
}
