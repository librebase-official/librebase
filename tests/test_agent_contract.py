"""Executable contract for the hosted MCP agent onboarding surface."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text()


def test_hosted_mcp_auth_tools_are_publicly_documented_and_reachable():
    route = read("data-studio-ui/app/api/mcp/route.ts")
    docs = read("data-studio-ui/app/for-agents/page.tsx")
    llms = read("data-studio-ui/app/llms.txt/route.ts")
    assert 'name: "auth_start"' in route
    assert 'name: "auth_poll"' in route
    assert 'Call <Code>auth_start</Code>' in docs
    assert "auth_start" in llms and "auth_poll" in llms


def test_auth_start_is_not_blocked_by_bearer_guard():
    route = read("data-studio-ui/app/api/mcp/route.ts")
    start = route.index("export async function POST")
    auth = route.index('case "auth_start"')
    guard = route.index("Missing Authorization", start)
    # The route must dispatch auth_start before the key-only guard, or explicitly
    # exempt it. This fails against the current unconditional guard.
    assert "auth_start" in route[route.index("const token", start):guard] or auth < guard


def test_agent_urls_in_sitemap_exist_on_their_declared_site():
    sitemap = read("../librebase-landing/app/sitemap.ts")
    assert "https://app.librebase.xyz/setup" in sitemap
    assert "https://app.librebase.xyz/for-agents" not in sitemap


def test_mcp_metadata_uses_repository_version_and_matches_tool_count():
    route = read("data-studio-ui/app/api/mcp/route.ts")
    version = (ROOT / "VERSION").read_text().strip()
    assert f'version: "{version}"' not in route
    assert "appVersion()" in route
    assert "toolCount: TOOLS.length" in route
