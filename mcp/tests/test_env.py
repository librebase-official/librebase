"""Tests for LIBREBASE_MCP_KEY → LIBREBASE_MCP_TOKEN env compatibility."""

from __future__ import annotations

import io
import os
import unittest
from contextlib import redirect_stderr
from librebase_mcp.bridge import HostedBridge
from librebase_mcp.env import (
    DEPRECATION_LINE,
    reset_mcp_env_deprecation_warning_for_tests,
    resolve_mcp_session_token,
)


class McpEnvCompatTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_mcp_env_deprecation_warning_for_tests()
        self._saved = {
            k: os.environ.get(k)
            for k in ("LIBREBASE_MCP_TOKEN", "LIBREBASE_MCP_KEY")
        }
        for key in self._saved:
            os.environ.pop(key, None)

    def tearDown(self) -> None:
        for key, val in self._saved.items():
            if val is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = val
        reset_mcp_env_deprecation_warning_for_tests()

    def test_legacy_key_alone_works_and_warns_once(self) -> None:
        os.environ["LIBREBASE_MCP_KEY"] = "lb_mcp_legacy_only"
        buf = io.StringIO()
        with redirect_stderr(buf):
            self.assertEqual(resolve_mcp_session_token(), "lb_mcp_legacy_only")
            self.assertEqual(resolve_mcp_session_token(), "lb_mcp_legacy_only")
        lines = [ln for ln in buf.getvalue().splitlines() if ln.strip()]
        self.assertEqual(lines, [DEPRECATION_LINE])
        self.assertNotIn("lb_mcp_legacy_only", buf.getvalue())

    def test_token_wins_when_both_set_without_warning(self) -> None:
        os.environ["LIBREBASE_MCP_KEY"] = "lb_mcp_old"
        os.environ["LIBREBASE_MCP_TOKEN"] = "lb_mcp_new"
        buf = io.StringIO()
        with redirect_stderr(buf):
            self.assertEqual(resolve_mcp_session_token(), "lb_mcp_new")
        self.assertEqual(buf.getvalue(), "")

    def test_bridge_uses_legacy_key_from_env(self) -> None:
        os.environ["LIBREBASE_MCP_KEY"] = "lb_mcp_from_key"
        bridge = HostedBridge(url="http://127.0.0.1:9/nope")
        self.assertEqual(bridge.get_session_token(), "lb_mcp_from_key")


if __name__ == "__main__":
    unittest.main()
