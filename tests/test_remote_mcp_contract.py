from pathlib import Path

ROOT = Path(__file__).parents[1]
STUDIO = ROOT / "data-studio-ui"


def read(path: str) -> str:
    return (STUDIO / path).read_text(encoding="utf-8")


def test_remote_discovery_is_primary_and_oauth_is_advertised():
    discovery = read("app/.well-known/mcp.json/route.ts")
    oauth = read("app/.well-known/oauth-authorization-server/route.ts")
    assert 'type: "http"' in discovery
    assert "/api/mcp" in discovery
    assert "authorization_server" in discovery
    assert "authorization_endpoint" in oauth
    assert "token_endpoint" in oauth
    assert "code_challenge_methods_supported" in oauth


def test_mcp_public_protocol_and_auth_calls_have_a_metadata_challenge():
    route = read("app/api/mcp/route.ts")
    assert 'toolName === "auth_start"' in route
    assert 'toolName === "auth_poll"' in route
    assert 'method === "initialize" || method === "tools/list"' in route
    assert "WWW-Authenticate" in route
    assert "oauth-authorization-server" in route


def test_discovery_does_not_advertise_local_stdio_as_the_primary_server():
    discovery = read("app/.well-known/mcp.json/route.ts")
    primary = discovery.split("fallback:", 1)[0]
    assert 'type: "http"' in primary
    assert 'command: "python3"' not in primary


def test_interactive_docs_do_not_require_a_pasted_key():
    docs = read("app/for-agents/page.tsx") + read("app/llms.txt/route.ts")
    assert "browser" in docs.lower()
    assert "never" in docs.lower() and "pasted" in docs.lower()
    assert "LIBREBASE_MCP_KEY" in docs
    assert "CI-only-static-key" not in docs
