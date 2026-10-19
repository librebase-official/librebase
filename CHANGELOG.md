# Changelog

## Unreleased

- **MCP env:** `LIBREBASE_MCP_TOKEN` is the canonical stdio-bridge bearer env var. `LIBREBASE_MCP_KEY` remains supported as a deprecated alias (token wins when both are set; one-line stderr warning when only the old name is used). Public agent docs (`llms.txt`, `/.well-known/mcp.json`, `/for-agents`) document `LIBREBASE_MCP_TOKEN` and hosted `Authorization: Bearer` auth.
- SDD `wave-a-native-io`: all Wave A contracts hard-gated (no soft skips); live 6/6 pass — [docs/release-notes/2026-07-30-wave-a-native-io-sdd.md](docs/release-notes/2026-07-30-wave-a-native-io-sdd.md)
- Librebase Admin API in-repo (`admin-api/`) — product management backend
- Studio `/setup` and `/admin` routes
- `@librebase/cli` and `@librebase/mcp` packages
- Capability matrix + parity plan docs
- Rename operator client from liorg → Librebase Admin branding
