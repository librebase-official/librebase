/**
 * MCP session unit tests — in-memory session state (no server needed).
 */
import assert from "node:assert/strict";
import {
  clearAdminSession,
  clearProjectSession,
  getAdminOrgId,
  getAdminToken,
  getProjectToken,
  sessionSummary,
  setAdminSession,
  setProjectSession,
} from "../src/session.js";

export async function run() {
  // starts unauthenticated (no env in this process)
  assert.equal(getAdminToken(), null);
  assert.equal(sessionSummary().adminAuthenticated, false);

  // login persists token + org
  setAdminSession("tok-abc-123", "org_1");
  assert.equal(getAdminToken(), "tok-abc-123");
  assert.equal(getAdminOrgId(), "org_1");
  assert.equal(sessionSummary().adminAuthenticated, true);
  assert.match(sessionSummary().adminTokenPrefix, /^tok-abc-123…/);

  // logout clears admin but not project
  setProjectSession("proj-tok");
  assert.equal(getProjectToken(), "proj-tok");
  clearAdminSession();
  assert.equal(getAdminToken(), null);
  assert.equal(getAdminOrgId(), null);
  assert.equal(getProjectToken(), "proj-tok");
  assert.equal(sessionSummary().projectSession, true);

  clearProjectSession();
  assert.equal(getProjectToken(), null);
  assert.equal(sessionSummary().projectSession, false);

  // setAdminSession without org keeps existing org? No: only sets when truthy
  setAdminSession("tok2");
  assert.equal(getAdminOrgId(), null);

  console.log("mcp session unit ok");
}

if (process.argv[1] === new URL(import.meta.url).pathname) {
  run().then(() => process.exit(0)).catch((e) => { console.error(e); process.exit(1); });
}
