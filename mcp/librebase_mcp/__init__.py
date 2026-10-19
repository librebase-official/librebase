"""Librebase stdio MCP server package."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("librebase-mcp")
except PackageNotFoundError:
    from pathlib import Path

    _version_file = Path(__file__).resolve().parents[1] / "VERSION"
    __version__ = _version_file.read_text(encoding="utf-8").strip() if _version_file.is_file() else "0.0.0"

__all__ = ["__version__"]
