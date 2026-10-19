"""In-process HTTP shim mimicking hosted MCP for bridge integration tests."""

from __future__ import annotations

import json
import os
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

TOOLS: list[dict[str, Any]] = [
    {"name": "org_whoami", "description": "", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "project_list", "description": "", "inputSchema": {"type": "object", "properties": {}}},
    {
        "name": "project_create",
        "description": "",
        "inputSchema": {
            "type": "object",
            "required": ["name", "instanceId"],
            "properties": {
                "name": {"type": "string"},
                "instanceId": {"type": "string"},
                "region": {"type": "string"},
                "deploymentMode": {"type": "string"},
            },
        },
    },
    {
        "name": "auth_provider_list",
        "description": "",
        "inputSchema": {
            "type": "object",
            "required": ["projectId"],
            "properties": {"projectId": {"type": "string"}},
        },
    },
    {
        "name": "auth_provider_upsert",
        "description": "",
        "inputSchema": {
            "type": "object",
            "required": ["projectId", "provider", "clientId", "clientSecret", "redirectUris"],
            "properties": {
                "projectId": {"type": "string"},
                "provider": {"type": "string"},
                "clientId": {"type": "string"},
                "clientSecret": {"type": "string"},
                "redirectUris": {"type": "array", "items": {"type": "string"}},
                "enabled": {"type": "boolean"},
            },
        },
    },
    {"name": "instance_list", "description": "", "inputSchema": {"type": "object", "properties": {}}},
    {
        "name": "instance_get",
        "description": "",
        "inputSchema": {
            "type": "object",
            "required": ["instanceId"],
            "properties": {"instanceId": {"type": "string"}},
        },
    },
    {
        "name": "instance_create",
        "description": "",
        "inputSchema": {
            "type": "object",
            "required": ["name"],
            "properties": {"name": {"type": "string"}, "region": {"type": "string"}},
        },
    },
    {
        "name": "instance_launch",
        "description": "",
        "inputSchema": {
            "type": "object",
            "required": ["instanceId"],
            "properties": {"instanceId": {"type": "string"}},
        },
    },
    {
        "name": "instance_stop",
        "description": "",
        "inputSchema": {
            "type": "object",
            "required": ["instanceId"],
            "properties": {"instanceId": {"type": "string"}},
        },
    },
    {"name": "member_list", "description": "", "inputSchema": {"type": "object", "properties": {}}},
    {
        "name": "member_invite",
        "description": "",
        "inputSchema": {
            "type": "object",
            "required": ["email", "role"],
            "properties": {"email": {"type": "string"}, "role": {"type": "string"}},
        },
    },
    {
        "name": "member_update_role",
        "description": "",
        "inputSchema": {
            "type": "object",
            "required": ["userId", "role"],
            "properties": {"userId": {"type": "string"}, "role": {"type": "string"}},
        },
    },
    {"name": "host_list", "description": "", "inputSchema": {"type": "object", "properties": {}}},
    {
        "name": "host_create",
        "description": "",
        "inputSchema": {
            "type": "object",
            "required": ["name"],
            "properties": {"name": {"type": "string"}, "region": {"type": "string"}},
        },
    },
]


def _admin_url() -> str:
    return os.environ.get("LIBREBASE_ADMIN_URL", "http://127.0.0.1:54330").rstrip("/")


def _request(method: str, path: str, token: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    data = None if body is None else json.dumps(body).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {token}",
    }
    req = urllib.request.Request(f"{_admin_url()}{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = {"error": "http_error", "message": raw or str(exc), "status": exc.code}
        payload.setdefault("status", exc.code)
        return payload


def _org_id(token: str) -> str:
    payload = _request("GET", "/org/v1/mcp/org", token)
    org_id = str(payload.get("orgId", "")) if isinstance(payload, dict) else ""
    if not org_id:
        raise RuntimeError(json.dumps(payload))
    return org_id


def _clean(arguments: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in arguments.items() if v is not None and v != ""}


def call_tool(name: str, arguments: dict[str, Any], token: str) -> dict[str, Any]:
    org = _org_id(token)
    if name == "org_whoami":
        return _request("GET", "/org/v1/mcp/org", token)
    if name == "project_list":
        return _request("GET", f"/org/v1/orgs/{org}/projects", token)
    if name == "project_create":
        return _request("POST", f"/org/v1/orgs/{org}/projects", token, _clean(arguments))
    if name == "auth_provider_list":
        return _request(
            "GET",
            f"/org/v1/orgs/{org}/projects/{arguments['projectId']}/providers",
            token,
        )
    if name == "auth_provider_upsert":
        body = _clean(arguments)
        body.setdefault("enabled", True)
        return _request(
            "POST",
            f"/org/v1/orgs/{org}/projects/{body['projectId']}/providers",
            token,
            body,
        )
    if name == "instance_list":
        return _request("GET", f"/org/v1/orgs/{org}/instances", token)
    if name == "instance_get":
        return _request("GET", f"/org/v1/orgs/{org}/instances/{arguments['instanceId']}", token)
    if name == "instance_create":
        body = _clean(arguments)
        body.setdefault("status", "stopped")
        return _request("POST", f"/org/v1/orgs/{org}/instances", token, body)
    if name == "instance_launch":
        return _request(
            "PATCH",
            f"/org/v1/orgs/{org}/instances/{arguments['instanceId']}",
            token,
            {"status": "running"},
        )
    if name == "instance_stop":
        return _request(
            "PATCH",
            f"/org/v1/orgs/{org}/instances/{arguments['instanceId']}",
            token,
            {"status": "stopped"},
        )
    if name == "member_list":
        return _request("GET", f"/org/v1/orgs/{org}/members", token)
    if name == "member_invite":
        return _request("POST", f"/org/v1/orgs/{org}/invites", token, _clean(arguments))
    if name == "member_update_role":
        return _request("PATCH", f"/org/v1/members/{arguments['userId']}", token, _clean(arguments))
    if name == "host_list":
        return _request("GET", f"/org/v1/orgs/{org}/hosts", token)
    if name == "host_create":
        return _request("POST", f"/org/v1/orgs/{org}/hosts", token, _clean(arguments))
    return {"error": "not_found", "message": f"unknown tool {name}"}


class _ShimHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        return

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8")
        try:
            msg = json.loads(raw)
        except json.JSONDecodeError:
            self.send_response(400)
            self.end_headers()
            return

        method = msg.get("method")
        req_id = msg.get("id")
        auth = self.headers.get("Authorization", "")
        token = ""
        if auth.lower().startswith("bearer "):
            token = auth[7:].strip()

        if method == "initialize":
            body = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "hosted-mcp-shim", "version": "test"},
                },
            }
        elif method == "notifications/initialized":
            self.send_response(204)
            self.end_headers()
            return
        elif method == "tools/list":
            body = {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}
        elif method == "tools/call":
            params = msg.get("params") or {}
            tool_name = str(params.get("name", ""))
            args = dict(params.get("arguments") or {})
            if not token:
                self.send_response(401)
                self.send_header("Content-Type", "application/json")
                payload = json.dumps({"error": "Missing Authorization: Bearer <mcp_key>"}).encode()
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
                return
            try:
                payload = call_tool(tool_name, args, token)
            except Exception as exc:  # noqa: BLE001
                payload = {"error": "tool_error", "message": str(exc)}
            body = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"content": [{"type": "text", "text": json.dumps(payload)}]},
            }
        else:
            body = {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"method not found: {method}"},
            }

        payload = json.dumps(body).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


class HostedMcpShim:
    def __init__(self, url: str, server: HTTPServer) -> None:
        self.url = url
        self._server = server

    def shutdown(self) -> None:
        self._server.shutdown()
        self._server.server_close()


def start_hosted_mcp_shim() -> HostedMcpShim:
    server = HTTPServer(("127.0.0.1", 0), _ShimHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return HostedMcpShim(f"http://127.0.0.1:{port}/api/mcp", server)
