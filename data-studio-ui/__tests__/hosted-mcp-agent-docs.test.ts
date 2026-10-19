import path from "node:path";
import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";

import { llmsBody } from "@/app/llms.txt/route";
import { appRouterPathExists, extractSitePathsFromLlmsBody } from "@/lib/app-router-path-exists";
import {
  assertHostedMcpDocGroupsMatchManifest,
  formatLlmsHostedMcpToolsSection,
  hostedMcpToolNamesFromDocGroups,
} from "@/lib/hosted-mcp-tool-docs";
import { HOSTED_MCP_TOOL_NAMES } from "@/lib/hosted-mcp-tools";
import { SITE_URL } from "@/lib/site";

const APP_DIR = path.join(__dirname, "..", "app");

describe("hosted MCP agent docs sync", () => {
  it("doc groups cover the hosted MCP manifest exactly", () => {
    assertHostedMcpDocGroupsMatchManifest();
    expect(hostedMcpToolNamesFromDocGroups().sort()).toEqual([...HOSTED_MCP_TOOL_NAMES].sort());
  });

  it("llms.txt Tools section matches the hosted MCP manifest", () => {
    const body = llmsBody();
    const toolsSection = body.split("## Tools\n")[1]?.split("\n## Security")[0]?.trim();
    expect(toolsSection).toBe(formatLlmsHostedMcpToolsSection());
  });

  it("for-agents page renders tools from the shared doc groups", () => {
    const source = readFileSync(path.join(APP_DIR, "for-agents", "page.tsx"), "utf8");
    expect(source).toContain("HOSTED_MCP_TOOL_DOC_GROUPS");
    expect(source).toContain("HOSTED_MCP_TOOL_COUNT");
    expect(hostedMcpToolNamesFromDocGroups().sort()).toEqual([...HOSTED_MCP_TOOL_NAMES].sort());
  });

  it("llms.txt internal URLs map to existing App Router pages or routes", () => {
    const body = llmsBody();
    const paths = extractSitePathsFromLlmsBody(body, SITE_URL);
    expect(paths.length).toBeGreaterThan(0);

    const missing = paths.filter((p) => !appRouterPathExists(APP_DIR, p));
    expect(missing, `missing routes for: ${missing.join(", ")}`).toEqual([]);
  });
});
