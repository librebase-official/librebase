/**
 * Librebase MCP session state.
 *
 * Holds the authenticated Admin API token + active org id after `admin_login`
 * or `admin_setup`, so subsequent admin tools authenticate without requiring a
 * manually-set LIBREBASE_ADMIN_SESSION env var. In-memory per MCP process.
 */

const state = {
  adminToken:
    process.env.LIBREBASE_ADMIN_SESSION ?? process.env.LIBREBASE_ORG_SESSION ?? null,
  adminOrgId: process.env.LIBREBASE_ORG_ID ?? null,
  projectToken: process.env.LIBREBASE_PROJECT_SESSION ?? null,
};

export function getAdminToken() {
  return state.adminToken;
}

export function setAdminSession(token, orgId) {
  state.adminToken = token;
  if (orgId) state.adminOrgId = orgId;
}

export function clearAdminSession() {
  state.adminToken = null;
  state.adminOrgId = null;
}

export function getAdminOrgId() {
  return state.adminOrgId;
}

export function getProjectToken() {
  return state.projectToken;
}

export function setProjectSession(token) {
  state.projectToken = token;
}

export function clearProjectSession() {
  state.projectToken = null;
}

export function sessionSummary() {
  return {
    adminAuthenticated: Boolean(state.adminToken),
    adminOrgId: state.adminOrgId,
    adminTokenPrefix: state.adminToken ? `${state.adminToken.slice(0, 12)}…` : null,
    projectSession: Boolean(state.projectToken),
  };
}
