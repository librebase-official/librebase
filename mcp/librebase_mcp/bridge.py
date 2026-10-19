"""Stdio → hosted MCP HTTP bridge (no local tool catalog)."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

DEFAULT_MCP_URL = "https://app.librebase.xyz/api/mcp"

_PUBLIC_TOOL_CALLS = frozenset({"auth_start", "auth_poll"})
_PUBLIC_METHODS = frozenset({"initialize", "notifications/initialized", "tools/list"})


class HostedBridge:
    def __init__(
        self,
        url: str | None = None,
        token: str | None = None,
    ) -> None:
        self.mcp_url = (url or os.environ.get("LIBREBASE_MCP_URL") or DEFAULT_MCP_URL).rstrip(
            "/"
        )
        self._session_token = (token or os.environ.get("LIBREBASE_MCP_TOKEN") or "").strip()

    def set_mcp_url(self, url: str) -> None:
        self.mcp_url = url.rstrip("/")

    def get_session_token(self) -> str:
        return self._session_token

    def set_session_token(self, token: str) -> None:
        self._session_token = (token or "").strip()

    def _auth_headers(self, method: str, params: dict[str, Any] | None) -> dict[str, str]:
        params = params or {}
        tool_name = str(params.get("name", "")) if method == "tools/call" else ""
        is_public = method in _PUBLIC_METHODS or (
            method == "tools/call" and tool_name in _PUBLIC_TOOL_CALLS
        )
        if is_public or not self._session_token:
            return {}
        return {"Authorization": f"Bearer {self._session_token}"}

    def _try_capture_token(self, result: dict[str, Any], tool_name: str) -> None:
        if tool_name != "auth_poll":
            return
        content = result.get("content")
        if not isinstance(content, list) or not content:
            return
        text = content[0].get("text") if isinstance(content[0], dict) else None
        if not isinstance(text, str):
            return
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            return
        if isinstance(payload, dict):
            access = payload.get("accessToken")
            if isinstance(access, str) and access:
                self._session_token = access

    def hosted_json_rpc(
        self,
        method: str,
        params: dict[str, Any] | None,
        req_id: str | int | None,
    ) -> dict[str, Any] | None:
        body = {"jsonrpc": "2.0", "method": method, "params": params or {}, "id": req_id}
        data = json.dumps(body).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            **self._auth_headers(method, params),
        }
        req = urllib.request.Request(
            self.mcp_url,
            data=data,
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                if resp.status == 204:
                    return None
                raw = resp.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8")
            try:
                parsed = json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                parsed = {"error": raw or str(exc)}
            if isinstance(parsed, dict) and "jsonrpc" in parsed:
                return parsed
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32000, "message": f"hosted_http_{exc.code}"},
            }
        except urllib.error.URLError as exc:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32000, "message": f"hosted_unreachable: {exc.reason}"},
            }

        if not raw:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32000, "message": "hosted_empty_response"},
            }
        try:
            msg = json.loads(raw)
        except json.JSONDecodeError:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32000, "message": "hosted_invalid_json"},
            }

        if method == "tools/call" and isinstance(msg.get("result"), dict):
            tool_name = str((params or {}).get("name", ""))
            self._try_capture_token(msg["result"], tool_name)
        return msg

    def list_tools(self) -> list[dict[str, Any]]:
        res = self.hosted_json_rpc("tools/list", {}, "bridge-list-tools")
        if not res or res.get("error"):
            err = res.get("error") if res else {"message": "no response"}
            raise RuntimeError(str(err.get("message", "tools/list failed")))
        tools = res.get("result", {}).get("tools")
        return tools if isinstance(tools, list) else []

    def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        res = self.hosted_json_rpc(
            "tools/call",
            {"name": name, "arguments": arguments},
            f"bridge-call-{name}",
        )
        if not res or res.get("error"):
            err = res.get("error") if res else {"message": "no response"}
            raise RuntimeError(str(err.get("message", f"tools/call {name} failed")))
        result = res.get("result")
        return result if isinstance(result, dict) else {}
