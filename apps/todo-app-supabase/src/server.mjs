#!/usr/bin/env node
/**
 * Todo app HTTP server — Supabase backend.
 *
 * Env:
 *   PORT                listen port (default 8788)
 *   LIBREBASE_API       Supabase project URL (default https://supabase.obsevia.com)
 *   LIBREBASE_ANON      Supabase anon key (required)
 *   LIBREBASE_SERVICE_ROLE  service_role key (for confirmed bench users, optional)
 *
 * Routes (same as the lis-backed app):
 *   GET  /              web UI
 *   GET  /health
 *   POST /auth/signup   { email, password }
 *   POST /auth/signin   { email, password }
 *   GET  /todos         (Bearer)
 *   POST /todos         { title } (Bearer)
 *   POST /todos/:id/complete (Bearer)
 *   DELETE /todos/:id   (Bearer)
 */

import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createSupabaseTodoApp } from "./app.mjs";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const INDEX_HTML = path.resolve(__dirname, "..", "public", "index.html");

const PORT = Number(process.env.PORT ?? 8788);
const API = process.env.LIBREBASE_API ?? "https://supabase.obsevia.com";
const ANON = process.env.LIBREBASE_ANON ?? "";

const app = createSupabaseTodoApp(API, ANON);

function json(res, status, body) {
  const payload = JSON.stringify(body);
  res.writeHead(status, { "Content-Type": "application/json", "Content-Length": Buffer.byteLength(payload) });
  res.end(payload);
}

function html(res, status, content) {
  res.writeHead(status, { "Content-Type": "text/html; charset=utf-8", "Content-Length": Buffer.byteLength(content) });
  res.end(content);
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

/** Decode JWT payload to get the user id (sub) for RLS on insert. */
function subFrom(token) {
  try {
    const payload = token.split(".")[1];
    const b64 = payload.replace(/-/g, "+").replace(/_/g, "/");
    const pad = b64.length % 4 ? "=".repeat(4 - (b64.length % 4)) : "";
    return JSON.parse(Buffer.from(b64 + pad, "base64").toString()).sub;
  } catch {
    return null;
  }
}

async function handler(req, res) {
  const url = new URL(req.url, `http://${req.headers.host}`);
  const route = url.pathname;
  const method = req.method;

  try {
    if (route === "/") {
      return html(res, 200, readFileSync(INDEX_HTML, "utf8"));
    }
    if (route === "/health") {
      return json(res, 200, { ok: true, service: "todo-app-supabase" });
    }
    if (method === "POST" && route === "/auth/signup") {
      const { email, password } = await readBody(req);
      const out = await app.auth.signUp(email, password);
      return json(res, 201, { user: out.user, access_token: out.session?.access_token });
    }
    if (method === "POST" && route === "/auth/signin") {
      const { email, password } = await readBody(req);
      const out = await app.auth.signIn(email, password);
      return json(res, 200, { user: out.user, access_token: out.session?.access_token });
    }

    if (method === "GET" && route === "/todos") {
      const token = bearer(req);
      if (!token) return json(res, 401, { error: "unauthorized" });
      const todos = await app.todos.list();
      return json(res, 200, { todos });
    }
    if (method === "POST" && route === "/todos") {
      const token = bearer(req);
      if (!token) return json(res, 401, { error: "unauthorized" });
      const userId = subFrom(token);
      const { title } = await readBody(req);
      const todo = await app.todos.create(title, userId);
      return json(res, 201, { todo });
    }
    const completeMatch = /^\/todos\/([^/]+)\/complete$/.exec(route);
    if (method === "POST" && completeMatch) {
      const token = bearer(req);
      if (!token) return json(res, 401, { error: "unauthorized" });
      const todo = await app.todos.complete(completeMatch[1]);
      return json(res, 200, { todo });
    }
    const delMatch = /^\/todos\/([^/]+)$/.exec(route);
    if (method === "DELETE" && delMatch) {
      const token = bearer(req);
      if (!token) return json(res, 401, { error: "unauthorized" });
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
  console.log(`todo-app-supabase listening on :${PORT} → ${API}`);
});
