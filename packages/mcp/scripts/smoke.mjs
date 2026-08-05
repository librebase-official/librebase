#!/usr/bin/env node
/**
 * MCP tool-surface smoke (no live Admin required).
 * Verifies tools.js exposes DoD tools and handlers exist in server.js.
 */
import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const toolsSrc = readFileSync(path.join(root, "src", "tools.js"), "utf8");
const serverSrc = readFileSync(path.join(root, "src", "server.js"), "utf8");

const required = [
  "admin_health",
  "admin_setup",
  "admin_login",
  "create_instance",
  "create_project",
  "list_projects",
  "parity_run",
  "matrix_status",
];

const missing = required.filter((name) => !toolsSrc.includes(`name: "${name}"`));
if (missing.length) {
  console.error("FAIL: missing tools", missing);
  process.exit(1);
}

const missingHandlers = required.filter((name) => !serverSrc.includes(`name === "${name}"`));
if (missingHandlers.length) {
  console.error("FAIL: missing handlers", missingHandlers);
  process.exit(1);
}

console.log(JSON.stringify({ ok: true, tools: required.length }));
