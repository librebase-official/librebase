"use client";

import { useState } from "react";
import { Button } from "@/components/ui";
import { copyText } from "@/lib/clipboard";
import { IconCopy, IconCheck } from "@/components/studio/icons";

interface HandoffPromptProps {
  orgId: string;
  projectId: string;
  projectName: string;
  instanceId: string;
  deploymentMode: string;
  region: string;
  apiUrl?: string | null;
  postgresUrl?: string | null;
}

export function HandoffPrompt({
  orgId,
  projectId,
  projectName,
  instanceId,
  deploymentMode,
  region,
  apiUrl,
  postgresUrl,
}: HandoffPromptProps) {
  const [copied, setCopied] = useState(false);
  const consoleUrl = process.env.NEXT_PUBLIC_SITE_URL || "https://app.librebase.xyz";

  const lines: string[] = [];
  lines.push(`# Librebase project handoff`);
  lines.push(``);
  lines.push(`You are an autonomous agent. Take over setup for this Librebase project end-to-end and only surface business decisions to the user (billing, Hetzner token limits, destructive ops).`);
  lines.push(``);
  lines.push(`## Environment`);
  lines.push(`- Console: ${consoleUrl}`);
  lines.push(`- Org ID: ${orgId}`);
  lines.push(`- Project: "${projectName}" — ID: ${projectId}`);
  lines.push(`- Instance: ${instanceId} (${deploymentMode} runtime, region: ${region})`);
  lines.push(`- Console API base: ${consoleUrl.replace(/\/$/, "")}/api`);
  lines.push(``);
  lines.push(`## Agent auth`);
  lines.push(`Use the Librebase MCP. Call \`auth_start\`, have the user approve in the browser, then call \`auth_poll\`.`);
  lines.push(`That opens the user's browser so they can sign in and approve this agent.`);
  lines.push(`The credential is stored in the OS keychain. Never ask the user to paste an MCP key, and never put a key in this prompt or in chat.`);
  lines.push(``);
  lines.push(`## Connection info`);
  lines.push(`Refresh at any time: ${consoleUrl.replace(/\/$/, "")}/api/projects/${projectId}/connect`);
  if (apiUrl) lines.push(`- API URL: ${apiUrl}`);
  if (postgresUrl) lines.push(`- Postgres: ${postgresUrl}`);
  if (!apiUrl && !postgresUrl) {
    lines.push(`- Not provisioned yet. Start it first, then fetch /connect.`);
  }
  lines.push(``);
  lines.push(`## Steps`);
  lines.push(`1. Start the runtime: POST /api/projects/${projectId}/launch`);
  lines.push(`2. (Optional) Provision a real VM if local isn't enough:`);
  lines.push(`   POST /api/hosts { "name":"app-vm", "provider":"hetzner", "region":"nbg1", "memMb":1024 }`);
  lines.push(`3. Apply schema with MCP \`migration_apply\` (name + SQL) — do not paste DB keys; the admin API forwards SQL to the instance.`);
  lines.push(`   Verify with \`table_list\` / \`migration_list\`. Ad-hoc reads: \`sql_execute\`.`);
  lines.push(`4. Configure GitHub/Google for *project users* at /projects/${projectId}/auth/providers (not Studio login).`);
  lines.push(`   Save client ID/secret there. Users start at /api/projects/${projectId}/auth/oauth/start?provider=github|google&redirect_to=<app-url>`);
  lines.push(`5. Verify health: GET /api/projects/${projectId}/connect -> probe.reachable`);
  lines.push(``);
  lines.push(`Run autonomously. Come back only for: Stripe billing confirmations, Hetzner token/region limits, and explicit approval on destructive operations.`);

  const prompt = lines.join("\n");

  async function onCopy() {
    const ok = await copyText(prompt);
    if (ok) {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    }
  }

  return (
    <div className="agent-handoff">
      <div className="agent-handoff-bar">
        <span>Handoff prompt</span>
        <Button variant="ghost" size="sm" onClick={onCopy} aria-live="polite">
          {copied ? <><IconCheck width="14" height="14" /> Copied</> : <><IconCopy width="14" height="14" /> Copy</>}
        </Button>
      </div>
      <details>
        <summary>Preview</summary>
        <textarea readOnly value={prompt} rows={10} className="agent-handoff-pre" />
      </details>
    </div>
  );
}
