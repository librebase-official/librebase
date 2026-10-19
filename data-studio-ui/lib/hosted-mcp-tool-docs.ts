import { HOSTED_MCP_TOOL_NAMES, HOSTED_MCP_TOOLS } from "@/lib/hosted-mcp-tools";

export type HostedMcpToolDocGroup = {
  names: readonly string[];
  /** How tool names are joined in llms.txt (default comma). */
  llmsJoin?: "," | "/";
  /** Optional trailing note on the llms.txt bullet. */
  llmsSuffix?: string;
  /** Short note for /for-agents (optional). */
  forAgentsNote?: string;
};

/** Grouped tool rows shared by llms.txt and /for-agents (must cover every hosted tool exactly once). */
export const HOSTED_MCP_TOOL_DOC_GROUPS: readonly HostedMcpToolDocGroup[] = [
  {
    names: ["auth_start", "auth_poll"],
    llmsJoin: "/",
    llmsSuffix: "browser login + device flow (self-signup)",
    forAgentsNote: "browser device flow (no key required)",
  },
  {
    names: ["org_whoami", "project_list", "project_create"],
    llmsJoin: ",",
  },
  {
    names: ["auth_provider_list", "auth_provider_upsert"],
    llmsJoin: "/",
    llmsSuffix: "OAuth (github/google/grok); client secret is KMS-sealed, never returned",
  },
  {
    names: [
      "instance_list",
      "instance_get",
      "instance_create",
      "instance_launch",
      "instance_stop",
    ],
    llmsJoin: "/",
  },
  {
    names: ["member_list", "member_invite", "member_update_role"],
    llmsJoin: "/",
  },
  {
    names: ["host_list", "host_create"],
    llmsJoin: "/",
  },
  {
    names: [
      "key_list",
      "key_create",
      "key_get",
      "key_decrypt",
      "key_rotate",
      "key_update",
      "key_delete",
    ],
    llmsJoin: "/",
    llmsSuffix: "KMS secrets; use key_decrypt only inside the agent process",
    forAgentsNote: "KMS secrets; use key_decrypt only inside the agent process, never in chat",
  },
];

function formatToolNames(names: readonly string[], join: "," | "/"): string {
  const sep = join === "/" ? " / " : ", ";
  return names.map((n) => `\`${n}\``).join(sep);
}

/** Markdown bullets under `## Tools` in llms.txt. */
export function formatLlmsHostedMcpToolsSection(): string {
  return HOSTED_MCP_TOOL_DOC_GROUPS
    .map((group) => {
      const join = group.llmsJoin ?? ",";
      const tools = formatToolNames(group.names, join);
      return group.llmsSuffix ? `- ${tools} -- ${group.llmsSuffix}` : `- ${tools}`;
    })
    .join("\n");
}

/** Flat list of tool names documented for agents (derived from groups). */
export function hostedMcpToolNamesFromDocGroups(): string[] {
  return HOSTED_MCP_TOOL_DOC_GROUPS.flatMap((g) => [...g.names]);
}

export function assertHostedMcpDocGroupsMatchManifest(): void {
  const fromGroups = new Set(hostedMcpToolNamesFromDocGroups());
  const manifest = new Set(HOSTED_MCP_TOOL_NAMES);
  const missing = HOSTED_MCP_TOOL_NAMES.filter((n) => !fromGroups.has(n));
  const extra = [...fromGroups].filter((n) => !manifest.has(n));
  if (missing.length || extra.length) {
    throw new Error(
      `Hosted MCP doc groups drift from manifest: missing=${missing.join(",")} extra=${extra.join(",")}`,
    );
  }
  if (fromGroups.size !== manifest.size) {
    throw new Error("Hosted MCP doc groups list duplicate tool names");
  }
}

export const HOSTED_MCP_TOOL_COUNT = HOSTED_MCP_TOOLS.length;
