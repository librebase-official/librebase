"""Librebase stdio MCP server — maintain users, instances, and projects.

Auth: LIBREBASE_MCP_KEY (an lb_mcp_... key from the console) + LIBREBASE_ADMIN_URL.
The key is org-scoped; the org id is resolved once from GET /org/v1/mcp/org.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any

_ADMIN_URL = os.environ.get("LIBREBASE_ADMIN_URL", "http://127.0.0.1:54330").rstrip("/")
_MCP_KEY = os.environ.get("LIBREBASE_MCP_KEY", "").strip()

_org_cache: str | None = None


def _request(
    method: str,
    path: str,
    body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    url = f"{_ADMIN_URL}{path}"
    data = None if body is None else json.dumps(body).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {_MCP_KEY}",
    }
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
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


def _org_id() -> str:
    global _org_cache
    if _org_cache is None:
        payload = _request("GET", "/org/v1/mcp/org")
        _org_cache = str(payload.get("orgId", "")) if isinstance(payload, dict) else ""
    if not _org_cache:
        raise RuntimeError("could not resolve org from MCP key")
    return _org_cache


TOOLS: list[dict[str, Any]] = [
    {
        "name": "org_whoami",
        "description": "Resolve the MCP key's org (id, name, edition).",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "project_list",
        "description": "List projects in the org.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "project_create",
        "description": "Create a project (requires an existing instanceId).",
        "inputSchema": {
            "type": "object",
            "required": ["name", "instanceId"],
            "properties": {
                "name": {"type": "string"},
                "instanceId": {"type": "string"},
                "region": {"type": "string"},
                "deploymentMode": {"type": "string", "enum": ["dedicated", "shared"]},
            },
        },
    },
    {
        "name": "auth_provider_list",
        "description": "List OAuth sign-in providers configured for a project.",
        "inputSchema": {
            "type": "object",
            "required": ["projectId"],
            "properties": {"projectId": {"type": "string"}},
        },
    },
    {
        "name": "auth_provider_upsert",
        "description": (
            "Configure (upsert) an OAuth sign-in provider for a project. "
            "The client secret is KMS-sealed server-side; it is never returned."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["projectId", "provider", "clientId", "clientSecret", "redirectUris"],
            "properties": {
                "projectId": {"type": "string"},
                "provider": {"type": "string", "enum": ["github", "google", "grok"]},
                "clientId": {"type": "string"},
                "clientSecret": {"type": "string"},
                "redirectUris": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Callback URLs the provider may redirect to.",
                },
                "enabled": {"type": "boolean"},
            },
        },
    },
    {
        "name": "instance_list",
        "description": "List instances in the org.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "instance_get",
        "description": "Get one instance by id.",
        "inputSchema": {
            "type": "object",
            "required": ["instanceId"],
            "properties": {"instanceId": {"type": "string"}},
        },
    },
    {
        "name": "instance_create",
        "description": "Create an instance (stopped by default).",
        "inputSchema": {
            "type": "object",
            "required": ["name"],
            "properties": {
                "name": {"type": "string"},
                "region": {"type": "string"},
                "runtimeTarget": {"type": "string"},
                "deploymentMode": {"type": "string", "enum": ["dedicated", "shared"]},
                "memLimitMb": {"type": "integer"},
            },
        },
    },
    {
        "name": "instance_launch",
        "description": "Launch an instance (status -> running).",
        "inputSchema": {
            "type": "object",
            "required": ["instanceId"],
            "properties": {"instanceId": {"type": "string"}},
        },
    },
    {
        "name": "instance_stop",
        "description": "Stop an instance (status -> stopped).",
        "inputSchema": {
            "type": "object",
            "required": ["instanceId"],
            "properties": {"instanceId": {"type": "string"}},
        },
    },
    {
        "name": "member_list",
        "description": "List org members (users).",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "member_invite",
        "description": "Invite a user by email with a role.",
        "inputSchema": {
            "type": "object",
            "required": ["email", "role"],
            "properties": {
                "email": {"type": "string"},
                "role": {"type": "string", "enum": ["owner", "admin", "member"]},
            },
        },
    },
    {
        "name": "member_update_role",
        "description": "Update a member's role.",
        "inputSchema": {
            "type": "object",
            "required": ["userId", "role"],
            "properties": {
                "userId": {"type": "string"},
                "role": {"type": "string", "enum": ["owner", "admin", "member"]},
            },
        },
    },
    {
        "name": "host_list",
        "description": "List hosts in the org.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "host_create",
        "description": "Create a host (VM).",
        "inputSchema": {
            "type": "object",
            "required": ["name"],
            "properties": {
                "name": {"type": "string"},
                "region": {"type": "string"},
                "memMb": {"type": "integer"},
            },
        },
    },
]


def _clean(arguments: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in arguments.items() if v is not None and v != ""}


def _call_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    org = _org_id()
    if name == "org_whoami":
        return _request("GET", "/org/v1/mcp/org")
    if name == "project_list":
        return _request("GET", f"/org/v1/orgs/{org}/projects")
    if name == "project_create":
        return _request("POST", f"/org/v1/orgs/{org}/projects", _clean(arguments))
    if name == "auth_provider_list":
        return _request(
            "GET",
            f"/org/v1/orgs/{org}/projects/{arguments['projectId']}/providers",
        )
    if name == "auth_provider_upsert":
        body = _clean(arguments)
        body.setdefault("enabled", True)
        return _request(
            "POST",
            f"/org/v1/orgs/{org}/projects/{body['projectId']}/providers",
            body,
        )
    if name == "instance_list":
        return _request("GET", f"/org/v1/orgs/{org}/instances")
    if name == "instance_get":
        return _request("GET", f"/org/v1/orgs/{org}/instances/{arguments['instanceId']}")
    if name == "instance_create":
        body = _clean(arguments)
        body.setdefault("status", "stopped")
        return _request("POST", f"/org/v1/orgs/{org}/instances", body)
    if name == "instance_launch":
        return _request(
            "PATCH",
            f"/org/v1/orgs/{org}/instances/{arguments['instanceId']}",
            {"status": "running"},
        )
    if name == "instance_stop":
        return _request(
            "PATCH",
            f"/org/v1/orgs/{org}/instances/{arguments['instanceId']}",
            {"status": "stopped"},
        )
    if name == "member_list":
        return _request("GET", f"/org/v1/orgs/{org}/members")
    if name == "member_invite":
        return _request("POST", f"/org/v1/orgs/{org}/invites", _clean(arguments))
    if name == "member_update_role":
        return _request("PATCH", f"/org/v1/members/{arguments['userId']}", _clean(arguments))
    if name == "host_list":
        return _request("GET", f"/org/v1/orgs/{org}/hosts")
    if name == "host_create":
        return _request("POST", f"/org/v1/orgs/{org}/hosts", _clean(arguments))
    return {"error": "not_found", "message": f"unknown tool {name}"}


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
                "serverInfo": {"name": "librebase", "version": "0.1.21"},
            },
        }
    if method == "notifications/initialized":
        return None
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}
    if method == "tools/call":
        params = msg.get("params") or {}
        tool_name = str(params.get("name", ""))
        args = dict(params.get("arguments") or {})
        try:
            payload = _call_tool(tool_name, args)
        except Exception as exc:  # noqa: BLE001
            payload = {"error": "tool_error", "message": str(exc)}
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"content": [{"type": "text", "text": json.dumps(payload, indent=2)}]},
        }
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
