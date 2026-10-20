"""MCP session token from environment (LIBREBASE_MCP_TOKEN, deprecated LIBREBASE_MCP_KEY)."""

from __future__ import annotations

import os
import sys

_KEY_DEPRECATION_WARNED = False

DEPRECATION_LINE = (
    "LIBREBASE_MCP_KEY is deprecated; use LIBREBASE_MCP_TOKEN instead."
)


def resolve_mcp_session_token() -> str:
    """Read bearer token from env. LIBREBASE_MCP_TOKEN wins when both are set."""
    global _KEY_DEPRECATION_WARNED  # noqa: PLW0603

    token = os.environ.get("LIBREBASE_MCP_TOKEN", "").strip()
    legacy = os.environ.get("LIBREBASE_MCP_KEY", "").strip()
    if token:
        return token
    if legacy:
        if not _KEY_DEPRECATION_WARNED:
            sys.stderr.write(f"{DEPRECATION_LINE}\n")
            _KEY_DEPRECATION_WARNED = True
        return legacy
    return ""


def reset_mcp_env_deprecation_warning_for_tests() -> None:
    """Test-only: allow deprecation warning to fire again."""
    global _KEY_DEPRECATION_WARNED  # noqa: PLW0603
    _KEY_DEPRECATION_WARNED = False
