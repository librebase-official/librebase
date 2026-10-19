"""Unit tests for librebase_mcp.bridge (mock hosted HTTP)."""

from __future__ import annotations

import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

from librebase_mcp.bridge import DEFAULT_MCP_URL, HostedBridge

SAMPLE_TOOLS = [
    {"name": "auth_start", "description": "d", "inputSchema": {"type": "object"}},
    {"name": "org_whoami", "description": "w", "inputSchema": {"type": "object"}},
]


class _Handler(BaseHTTPRequestHandler):
    calls: list[dict[str, Any]] = []

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        return

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8")
        msg = json.loads(raw)
        _Handler.calls.append(
            {"authorization": self.headers.get("Authorization"), "msg": msg}
        )
        method = msg.get("method")
        req_id = msg.get("id")
        if method == "tools/list":
            body = {"jsonrpc": "2.0", "id": req_id, "result": {"tools": SAMPLE_TOOLS}}
        elif method == "tools/call" and msg.get("params", {}).get("name") == "auth_start":
            body = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps({"deviceCode": "dc"}),
                        }
                    ]
                },
            }
        elif method == "tools/call" and msg.get("params", {}).get("name") == "auth_poll":
            body = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(
                                {"accessToken": "lb_agt_x", "status": "approved"}
                            ),
                        }
                    ]
                },
            }
        elif method == "tools/call":
            body = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"content": [{"type": "text", "text": '{"ok":true}'}]},
            }
        else:
            body = {"jsonrpc": "2.0", "id": req_id, "error": {"message": "bad"}}
        payload = json.dumps(body).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def _start_server() -> tuple[str, HTTPServer]:
    _Handler.calls = []
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    return f"http://{host}:{port}/api/mcp", server


class BridgeTests(unittest.TestCase):
    def test_list_forward_token_and_endpoint(self) -> None:
        url, server = _start_server()
        try:
            bridge = HostedBridge(url=url, token="tok-env")
            self.assertNotEqual(url, DEFAULT_MCP_URL.rstrip("/"))
            tools = bridge.list_tools()
            self.assertEqual(len(tools), 2)
            bridge.call_tool("org_whoami", {})
            auths = [c["authorization"] for c in _Handler.calls if c["msg"].get("method") == "tools/call"]
            self.assertTrue(any(a and "tok-env" in a for a in auths))
            list_calls = [c for c in _Handler.calls if c["msg"].get("method") == "tools/list"]
            self.assertEqual(list_calls[0]["authorization"], None)
        finally:
            server.shutdown()

    def test_device_flow_sets_session_token(self) -> None:
        url, server = _start_server()
        try:
            bridge = HostedBridge(url=url)
            bridge.call_tool("auth_start", {})
            bridge.call_tool("auth_poll", {"deviceCode": "dc"})
            self.assertEqual(bridge.get_session_token(), "lb_agt_x")
            _Handler.calls.clear()
            bridge.call_tool("org_whoami", {})
            self.assertIn("lb_agt_x", _Handler.calls[-1]["authorization"] or "")
        finally:
            server.shutdown()


if __name__ == "__main__":
    unittest.main()
