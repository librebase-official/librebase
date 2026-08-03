/**
 * MCP package smoke — tool surface includes parity_run + matrix_status.
 * Does not start the stdio server (no live Admin required).
 */
import assert from "node:assert/strict";
import { tools, TOOL_NAMES } from "../src/tools.js";

assert.ok(Array.isArray(tools) && tools.length > 0);
assert.ok(TOOL_NAMES.includes("parity_run"), "parity_run missing");
assert.ok(TOOL_NAMES.includes("matrix_status"), "matrix_status missing");
assert.ok(TOOL_NAMES.includes("admin_health"), "admin_health missing");

for (const t of tools) {
  assert.equal(typeof t.name, "string");
  assert.equal(typeof t.description, "string");
  assert.equal(typeof t.inputSchema, "object");
}

console.log("mcp smoke ok", TOOL_NAMES.length, "tools");
