/**
 * MCP session token from environment (LIBREBASE_MCP_TOKEN; deprecated LIBREBASE_MCP_KEY).
 */

let keyDeprecationWarned = false;

export const MCP_KEY_DEPRECATION_LINE =
  "LIBREBASE_MCP_KEY is deprecated; use LIBREBASE_MCP_TOKEN instead.";

/** @returns {string} Bearer token; LIBREBASE_MCP_TOKEN wins when both env vars are set. */
export function resolveMcpSessionToken() {
  const token = (process.env.LIBREBASE_MCP_TOKEN ?? "").trim();
  const legacy = (process.env.LIBREBASE_MCP_KEY ?? "").trim();
  if (token) {
    return token;
  }
  if (legacy) {
    if (!keyDeprecationWarned) {
      console.error(MCP_KEY_DEPRECATION_LINE);
      keyDeprecationWarned = true;
    }
    return legacy;
  }
  return "";
}

/** @internal Test helper */
export function resetMcpEnvDeprecationWarningForTests() {
  keyDeprecationWarned = false;
}
