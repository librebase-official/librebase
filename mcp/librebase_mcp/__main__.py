"""Librebase stdio MCP bridge — proxies to hosted Streamable HTTP MCP.

Env:
  LIBREBASE_MCP_URL   — default https://app.librebase.xyz/api/mcp
  LIBREBASE_MCP_TOKEN — optional lb_mcp_* / lb_agt_* bearer (never logged)
"""

from __future__ import annotations

import json
import sys
from typing import Any

from librebase_mcp import __version__
from librebase_mcp.bridge import HostedBridge

_bridge = HostedBridge()


def _handle(msg: dict[str, Any]) -> dict[str, Any] | None:
    method = msg.get("method")
    req_id = msg.get("id")

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "librebase-mcp-bridge", "version": __version__},
            },
        }
    if method == "notifications/initialized":
        return None

    if method == "tools/list":
        try:
            tools = _bridge.list_tools()
        except Exception as exc:  # noqa: BLE001
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32000, "message": str(exc)},
            }
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": tools}}

    if method == "tools/call":
        params = msg.get("params") or {}
        tool_name = str(params.get("name", ""))
        args = dict(params.get("arguments") or {})
        try:
            result = _bridge.call_tool(tool_name, args)
        except Exception as exc:  # noqa: BLE001
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": str(exc)}],
                    "isError": True,
                },
            }
        return {"jsonrpc": "2.0", "id": req_id, "result": result}

    if req_id is not None:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"method not found: {method}"},
        }
    return None


def main() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        out = _handle(msg)
        if out is not None:
            sys.stdout.write(json.dumps(out) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
