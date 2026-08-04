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
assert.ok(TOOL_NAMES.includes("execute_sql"), "execute_sql missing");
assert.ok(TOOL_NAMES.includes("list_tables"), "list_tables missing");
assert.ok(TOOL_NAMES.includes("list_storage_buckets"), "list_storage_buckets missing");
assert.ok(TOOL_NAMES.includes("list_edge_functions"), "list_edge_functions missing");
assert.ok(TOOL_NAMES.includes("get_auth_mfa_status"), "get_auth_mfa_status missing");
assert.ok(TOOL_NAMES.includes("list_auth_users"), "list_auth_users missing");
assert.ok(TOOL_NAMES.includes("create_auth_user"), "create_auth_user missing");
assert.ok(TOOL_NAMES.includes("apply_migration"), "apply_migration missing");
assert.ok(TOOL_NAMES.includes("get_logs"), "get_logs missing");

for (const t of tools) {
  assert.equal(typeof t.name, "string");
  assert.equal(typeof t.description, "string");
  assert.equal(typeof t.inputSchema, "object");
}

console.log("mcp smoke ok", TOOL_NAMES.length, "tools");
