#!/usr/bin/env node
/**
 * Todo app HTTP server — deployable on a Librebase instance.
 *
 * Env:
 *   PORT            listen port (default 8787)
 *   LIBREBASE_API   project API base (default http://127.0.0.1:54321)
 *   LIBREBASE_ANON  project anon/publishable key (default "anon")
 *
 * Routes:
 *   POST /auth/signup   { email, password }
 *   POST /auth/signin   { email, password }
 *   GET  /todos         (Bearer)
 *   POST /todos         { title } (Bearer)
 *   POST /todos/:id/complete (Bearer)
 *   DELETE /todos/:id   (Bearer)
 */

import { createTodoApp } from "./app.mjs";

const PORT = Number(process.env.PORT ?? 8787);
const API = process.env.LIBREBASE_API ?? "http://127.0.0.1:54321";
const ANON = process.env.LIBREBASE_ANON ?? "anon";

const app = createTodoApp(API, ANON);

function json(res, status, body) {
  const payload = JSON.stringify(body);
  res.writeHead(status, { "Content-Type": "application/json", "Content-Length": Buffer.byteLength(payload) });
  res.end(payload);
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    let data = "";
    req.on("data", (c) => { data += c; });
    req.on("end", () => {
      try { resolve(data ? JSON.parse(data) : {}); } catch (e) { reject(e); }
    });
    req.on("error", reject);
  });
}

function bearer(req) {
  const h = req.headers.authorization ?? "";
  return h.startsWith("Bearer ") ? h.slice(7) : null;
}

async function handler(req, res) {
  const url = new URL(req.url, `http://${req.headers.host}`);
  const route = url.pathname;
  const method = req.method;

  try {
    if (method === "POST" && route === "/auth/signup") {
      const { email, password } = await readBody(req);
      const out = await app.auth.signUp(email, password);
      return json(res, 201, { user: out.user });
    }
    if (method === "POST" && route === "/auth/signin") {
      const { email, password } = await readBody(req);
      const out = await app.auth.signIn(email, password);
      return json(res, 200, { user: out.user, access_token: out.session?.access_token });
    }

    if (method === "GET" && route === "/todos") {
      if (!bearer(req)) return json(res, 401, { error: "unauthorized" });
      const todos = await app.todos.list();
      return json(res, 200, { todos });
    }
    if (method === "POST" && route === "/todos") {
      if (!bearer(req)) return json(res, 401, { error: "unauthorized" });
      const { title } = await readBody(req);
      const todo = await app.todos.create(title);
      return json(res, 201, { todo });
    }
    const completeMatch = /^\/todos\/([^/]+)\/complete$/.exec(route);
    if (method === "POST" && completeMatch) {
      if (!bearer(req)) return json(res, 401, { error: "unauthorized" });
      const todo = await app.todos.complete(completeMatch[1]);
      return json(res, 200, { todo });
    }
    const delMatch = /^\/todos\/([^/]+)$/.exec(route);
    if (method === "DELETE" && delMatch) {
      if (!bearer(req)) return json(res, 401, { error: "unauthorized" });
      const out = await app.todos.remove(delMatch[1]);
      return json(res, 200, { deleted: true, ...(out ?? {}) });
    }

    json(res, 404, { error: "not_found", route });
  } catch (e) {
    const status = e.status ?? 500;
    json(res, status, { error: e.message ?? String(e) });
  }
}

const server = (await import("node:http")).createServer(handler);
server.listen(PORT, () => {
  console.log(`todo-app listening on :${PORT} → project api ${API}`);
});
