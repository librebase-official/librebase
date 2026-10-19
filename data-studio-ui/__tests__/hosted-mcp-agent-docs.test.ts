import path from "node:path";
import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";

import { llmsBody } from "@/app/llms.txt/route";
import { appRouterPathExists, extractSitePathsFromLlmsBody } from "@/lib/app-router-path-exists";
import {
  assertDocToolNamesMatchManifest,
  extractHostedMcpToolNamesFromForAgentsSource,
  extractHostedMcpToolNamesFromLlms,
  HOSTED_MCP_TOOL_COUNT,
  parseForAgentsHostedToolCount,
  parseLlmsHostedToolCount,
} from "@/lib/hosted-mcp-tool-docs";
import { HOSTED_MCP_TOOL_NAMES } from "@/lib/hosted-mcp-tools";
import { SITE_URL } from "@/lib/site";

const APP_DIR = path.join(__dirname, "..", "app");

describe("hosted MCP agent docs sync", () => {
  it("llms.txt Tools section lists the same names as tools/list", () => {
    const body = llmsBody();
    const documented = extractHostedMcpToolNamesFromLlms(body);
    assertDocToolNamesMatchManifest(documented, "llms.txt");
    expect(parseLlmsHostedToolCount(body)).toBe(HOSTED_MCP_TOOL_COUNT);
  });

  it("/for-agents lists the same tool names as tools/list", () => {
    const source = readFileSync(path.join(APP_DIR, "for-agents", "page.tsx"), "utf8");
    const documented = extractHostedMcpToolNamesFromForAgentsSource(source);
    assertDocToolNamesMatchManifest(documented, "/for-agents");
    expect(parseForAgentsHostedToolCount(source)).toBe(HOSTED_MCP_TOOL_COUNT);
  });

  it("hosted manifest tool count is stable for doc headers", () => {
    expect(HOSTED_MCP_TOOL_NAMES).toHaveLength(HOSTED_MCP_TOOL_COUNT);
  });

  it("llms.txt internal URLs map to existing App Router pages or routes", () => {
    const body = llmsBody();
    const paths = extractSitePathsFromLlmsBody(body, SITE_URL);
    expect(paths.length).toBeGreaterThan(0);

    const missing = paths.filter((p) => !appRouterPathExists(APP_DIR, p));
    expect(missing, `missing routes for: ${missing.join(", ")}`).toEqual([]);
  });
});
