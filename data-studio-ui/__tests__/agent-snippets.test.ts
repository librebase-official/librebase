import { describe, expect, it } from "vitest";
import { agentSnippets, mcpRemoteUrl } from "@/lib/agent-snippets";

describe("agent snippets", () => {
  it("prefers a remote MCP URL over local python", () => {
    expect(mcpRemoteUrl("https://app.librebase.xyz")).toBe(
      "https://app.librebase.xyz/mcp",
    );
    const snippets = agentSnippets({
      siteUrl: "https://app.librebase.xyz",
      mcpKey: "lb_mcp_test",
    });
    const cursor = snippets.find((s) => s.id === "cursor")!;
    expect(cursor.text).toContain("https://app.librebase.xyz/mcp");
    expect(cursor.text).toContain("Bearer lb_mcp_test");
    expect(cursor.text).not.toContain("python3");
    expect(cursor.text).not.toContain("PYTHONPATH");

    const claude = snippets.find((s) => s.id === "claude")!;
    expect(claude.text).toContain("claude mcp add --transport http");
    expect(claude.text).toContain("lb_mcp_test");
  });
});
