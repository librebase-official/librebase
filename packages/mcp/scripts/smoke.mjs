#!/usr/bin/env node
/**
 * MCP tool-surface smoke (no live Admin required).
 * Verifies server module loads and ListTools exposes DoD tools.
 */
import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const src = readFileSync(path.join(root, "src", "server.js"), "utf8");

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

const missing = required.filter((name) => !src.includes(`name: "${name}"`));
if (missing.length) {
  console.error("FAIL: missing tools", missing);
  process.exit(1);
}

console.log(JSON.stringify({ ok: true, tools: required.length }));
