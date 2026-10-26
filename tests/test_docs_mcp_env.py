"""Docs and discovery surfaces must match MCP env + tool manifest (LIB-164, LIB-165, LIB-149)."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DOC_PATHS = [
    ROOT / "README.md",
    ROOT / "mcp/README.md",
    ROOT / "packages/mcp/README.md",
    ROOT / "docs/self-hosting.md",
    ROOT / "docs/mcp/AUDIT.md",
    ROOT / "HANDOFF.md",
]

PUBLIC_AGENT_SOURCES = [
    ROOT / "data-studio-ui/app/for-agents/page.tsx",
    ROOT / "data-studio-ui/app/llms.txt/route.ts",
    ROOT / "data-studio-ui/app/.well-known/mcp.json/route.ts",
]

MANIFEST = ROOT / "data-studio-ui/lib/hosted-mcp-tools.ts"
AUDIT = ROOT / "docs/mcp/AUDIT.md"


def hosted_tool_names() -> list[str]:
    text = MANIFEST.read_text(encoding="utf-8")
    names = re.findall(r'name: "([a-z][a-z0-9_]*)"', text)
    # Drop interface field noise — only tool entries use lowercase snake names after "name:"
    return sorted(set(names))


def audit_catalog_tools() -> list[str]:
    text = AUDIT.read_text(encoding="utf-8")
    start = text.index("## Hosted tool catalog")
    end = text.index("## Stdio bridges")
    section = text[start:end]
    found = re.findall(r"`([a-z][a-z0-9_]*)`", section)
    manifest = set(hosted_tool_names())
    return sorted({n for n in found if n in manifest})


class TestDocsMcpEnv(unittest.TestCase):
    def test_public_surfaces_use_canonical_mcp_token_env(self) -> None:
        combined = "".join(p.read_text(encoding="utf-8") for p in PUBLIC_AGENT_SOURCES)
        self.assertIn("LIBREBASE_MCP_TOKEN", combined)
        self.assertNotIn("LIBREBASE_MCP_KEY", combined)
        self.assertNotIn("CI-only-static-key", combined)

    def test_no_ci_only_static_key_in_docs_tree(self) -> None:
        for path in DOC_PATHS:
            self.assertNotIn(
                "CI-only-static-key",
                path.read_text(encoding="utf-8"),
                msg=str(path),
            )

    def test_stdio_readmes_require_repo_checkout_until_publish(self) -> None:
        for rel in ("mcp/README.md", "packages/mcp/README.md"):
            text = (ROOT / rel).read_text(encoding="utf-8").lower()
            self.assertIn("repo checkout", text, msg=rel)
            self.assertIn("not published", text, msg=rel)

    def test_mcp_json_fallback_documents_checkout_requirement(self) -> None:
        route = (ROOT / "data-studio-ui/app/.well-known/mcp.json/route.ts").read_text(
            encoding="utf-8"
        )
        self.assertIn("repository checkout", route)
        self.assertIn("LIBREBASE_MCP_TOKEN", route)

    def test_audit_tool_catalog_matches_hosted_manifest(self) -> None:
        manifest = hosted_tool_names()
        documented = audit_catalog_tools()
        self.assertEqual(
            documented,
            manifest,
            f"docs/mcp/AUDIT.md drift: missing={set(manifest) - set(documented)} "
            f"extra={set(documented) - set(manifest)}",
        )

    def test_readme_agent_section_documents_token_not_key(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        agent = readme.split("## For AI agents (MCP)", 1)[1].split("## Self-hosting", 1)[0]
        self.assertIn("LIBREBASE_MCP_TOKEN", agent)
        self.assertNotIn("LIBREBASE_MCP_KEY", agent)


if __name__ == "__main__":
    unittest.main()
