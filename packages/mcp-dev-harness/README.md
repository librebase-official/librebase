# @librebase/mcp-dev-harness (private)

**Not published** (`private: true`). Local developer harness for Librebase Admin API, parity matrix, and Supabase-shaped project API probes.

Production agents should use:

- **Hosted MCP:** `https://app.librebase.xyz/api/mcp`
- **Stdio bridge (repo checkout):** `node packages/mcp/src/server.js` or `python3 -m librebase_mcp` — npm/PyPI packages not published yet (LIB-150)

## Run

```bash
cd packages/mcp-dev-harness
npm install
node src/server.js
```

Env: `LIBREBASE_ADMIN_URL`, `LIBREBASE_ROOT`, `LIBREBASE_PARITY_API`, etc. (see `src/server.js`).
