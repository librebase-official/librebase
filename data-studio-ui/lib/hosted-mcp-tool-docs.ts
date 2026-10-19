import { HOSTED_MCP_TOOL_NAMES, HOSTED_MCP_TOOLS } from "@/lib/hosted-mcp-tools";

export const HOSTED_MCP_TOOL_COUNT = HOSTED_MCP_TOOLS.length;

const LLMS_TOOLS_HEADER_RE = /## Tools \(live hosted tools\/list, (\d+)\)\n/;
const LLMS_TOOLS_END = "\n\nNot available on the hosted server today:";

/** Tool names backticked in llms.txt `## Tools (live hosted tools/list, N)` section. */
export function extractHostedMcpToolNamesFromLlms(body: string): string[] {
  const header = body.match(LLMS_TOOLS_HEADER_RE);
  if (!header) {
    throw new Error("llms.txt missing ## Tools (live hosted tools/list, N) section");
  }
  const start = body.indexOf(header[0]) + header[0].length;
  const end = body.indexOf(LLMS_TOOLS_END, start);
  if (end < 0) {
    throw new Error("llms.txt Tools section missing trailing Not available paragraph");
  }
  const section = body.slice(start, end);
  const names = new Set<string>();
  for (const match of section.matchAll(/`([a-z][a-z0-9_]*)`/g)) {
    names.add(match[1]);
  }
  return [...names].sort();
}

export function parseLlmsHostedToolCount(body: string): number | null {
  const m = body.match(LLMS_TOOLS_HEADER_RE);
  return m ? Number(m[1]) : null;
}

/** Tool names rendered as <Code>…</Code> on /for-agents that exist in the hosted manifest. */
export function extractHostedMcpToolNamesFromForAgentsSource(source: string): string[] {
  const manifest = new Set(HOSTED_MCP_TOOL_NAMES);
  const names = new Set<string>();
  for (const match of source.matchAll(/<Code>([^<]+)<\/Code>/g)) {
    const name = match[1].trim();
    if (manifest.has(name)) {
      names.add(name);
    }
  }
  return [...names].sort();
}

export function parseForAgentsHostedToolCount(source: string): number | null {
  const m = source.match(/Hosted MCP tools \((\d+)\)/);
  return m ? Number(m[1]) : null;
}

export function assertDocToolNamesMatchManifest(documented: string[], label: string): void {
  const docSet = new Set(documented);
  const manifest = [...HOSTED_MCP_TOOL_NAMES].sort();
  const missing = manifest.filter((n) => !docSet.has(n));
  const extra = documented.filter((n) => !HOSTED_MCP_TOOL_NAMES.includes(n));
  if (missing.length || extra.length || docSet.size !== manifest.length) {
    throw new Error(
      `${label} tool list drift: missing=${missing.join(",")} extra=${extra.join(",")}`,
    );
  }
}
