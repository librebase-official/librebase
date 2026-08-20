export type AgentSnippetId = "cursor" | "claude" | "grok";

export interface AgentSnippet {
  id: AgentSnippetId;
  label: string;
  hint: string;
  language: "json" | "bash";
  text: string;
}

export function mcpRemoteUrl(siteUrl: string): string {
  return `${siteUrl.replace(/\/$/, "")}/mcp`;
}

export function agentSnippets(opts: {
  siteUrl: string;
  mcpKey: string;
}): AgentSnippet[] {
  const url = mcpRemoteUrl(opts.siteUrl);
  const key = opts.mcpKey || "lb_mcp_YOUR_KEY";
  const cursor = {
    mcpServers: {
      librebase: {
        url,
        headers: { Authorization: `Bearer ${key}` },
      },
    },
  };
  return [
    {
      id: "cursor",
      label: "Cursor",
      hint: "Paste into ~/.cursor/mcp.json",
      language: "json",
      text: JSON.stringify(cursor, null, 2),
    },
    {
      id: "claude",
      label: "Claude",
      hint: "Run in a terminal, then restart Claude Code",
      language: "bash",
      text: `claude mcp add --transport http librebase ${url} --header "Authorization: Bearer ${key}"`,
    },
    {
      id: "grok",
      label: "Grok",
      hint: "Same JSON as Cursor — drop it in your MCP config",
      language: "json",
      text: JSON.stringify(cursor, null, 2),
    },
  ];
}
