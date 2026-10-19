/**
 * Canonical hosted MCP tool manifest (POST /api/mcp → tools/list).
 * Mirrors packages/mcp Python definitions.
 */
export interface HostedMcpTool {
  name: string;
  description: string;
  inputSchema: Record<string, unknown>;
}

export const HOSTED_MCP_TOOLS: HostedMcpTool[] = [
  {
    name: "org_whoami",
    description: "Resolve the MCP key's org (id, name, edition).",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "project_list",
    description: "List projects in the org.",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "project_create",
    description: "Create a project (requires an existing instanceId).",
    inputSchema: {
      type: "object",
      required: ["name", "instanceId"],
      properties: {
        name: { type: "string" },
        instanceId: { type: "string" },
        region: { type: "string" },
        deploymentMode: { type: "string", enum: ["dedicated", "shared"] },
      },
    },
  },
  {
    name: "auth_provider_list",
    description: "List OAuth sign-in providers configured for a project.",
    inputSchema: {
      type: "object",
      required: ["projectId"],
      properties: { projectId: { type: "string" } },
    },
  },
  {
    name: "auth_provider_upsert",
    description:
      "Configure an OAuth sign-in provider for a project. " +
      "The client secret is KMS-sealed server-side; it is never returned.",
    inputSchema: {
      type: "object",
      required: ["projectId", "provider", "clientId", "clientSecret", "redirectUris"],
      properties: {
        projectId: { type: "string" },
        provider: { type: "string", enum: ["github", "google", "grok"] },
        clientId: { type: "string" },
        clientSecret: { type: "string" },
        redirectUris: { type: "array", items: { type: "string" } },
        enabled: { type: "boolean" },
      },
    },
  },
  {
    name: "instance_list",
    description: "List instances in the org.",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "instance_get",
    description: "Get one instance by id.",
    inputSchema: {
      type: "object",
      required: ["instanceId"],
      properties: { instanceId: { type: "string" } },
    },
  },
  {
    name: "instance_create",
    description: "Create an instance (stopped by default).",
    inputSchema: {
      type: "object",
      required: ["name"],
      properties: {
        name: { type: "string" },
        region: { type: "string" },
        runtimeTarget: { type: "string" },
        deploymentMode: { type: "string", enum: ["dedicated", "shared"] },
        memLimitMb: { type: "integer" },
      },
    },
  },
  {
    name: "instance_launch",
    description: "Launch an instance (status -> running).",
    inputSchema: {
      type: "object",
      required: ["instanceId"],
      properties: { instanceId: { type: "string" } },
    },
  },
  {
    name: "instance_stop",
    description: "Stop an instance (status -> stopped).",
    inputSchema: {
      type: "object",
      required: ["instanceId"],
      properties: { instanceId: { type: "string" } },
    },
  },
  {
    name: "member_list",
    description: "List org members (users).",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "member_invite",
    description: "Invite a user by email with a role.",
    inputSchema: {
      type: "object",
      required: ["email", "role"],
      properties: {
        email: { type: "string" },
        role: { type: "string", enum: ["owner", "admin", "member"] },
      },
    },
  },
  {
    name: "member_update_role",
    description: "Update a member's role.",
    inputSchema: {
      type: "object",
      required: ["userId", "role"],
      properties: {
        userId: { type: "string" },
        role: { type: "string", enum: ["owner", "admin", "member"] },
      },
    },
  },
  {
    name: "host_list",
    description: "List hosts in the org.",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "host_create",
    description: "Create a host (VM).",
    inputSchema: {
      type: "object",
      required: ["name"],
      properties: {
        name: { type: "string" },
        region: { type: "string" },
        memMb: { type: "integer" },
      },
    },
  },
  {
    name: "auth_start",
    description:
      "Start MCP device authorization. User opens verificationUri (or verificationUriComplete), signs in with Google/GitHub, and approves. No MCP key needed.",
    inputSchema: {
      type: "object",
      properties: {
        clientName: { type: "string", description: "Shown on the approve screen (default: MCP Agent)" },
      },
    },
  },
  {
    name: "auth_poll",
    description:
      "Poll device authorization. Call after auth_start until accessToken is returned (lb_agt_*). Use that token as Bearer for other tools.",
    inputSchema: {
      type: "object",
      required: ["deviceCode"],
      properties: {
        deviceCode: { type: "string", description: "The deviceCode from auth_start" },
      },
    },
  },
  {
    name: "key_list",
    description: "List all KMS keys/secrets for the org. Returns key metadata (not values).",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "key_create",
    description: "Create a new KMS key/secret. The value is sealed in the KMS and shown only once.",
    inputSchema: {
      type: "object",
      required: ["name", "value"],
      properties: {
        name: { type: "string", description: "Human-readable key name" },
        value: { type: "string", description: "The secret value to store" },
        kind: { type: "string", enum: ["secret", "keypair"], description: "Key type (default: secret)" },
        projectId: { type: "string", description: "Optional project scope" },
      },
    },
  },
  {
    name: "key_get",
    description: "Get key metadata (name, kind, project). Does NOT return the value.",
    inputSchema: {
      type: "object",
      required: ["keyId"],
      properties: { keyId: { type: "string" } },
    },
  },
  {
    name: "key_decrypt",
    description: "Decrypt a key's value. Only the calling process sees the plaintext -- it is never shown to the model.",
    inputSchema: {
      type: "object",
      required: ["keyId"],
      properties: { keyId: { type: "string" } },
    },
  },
  {
    name: "key_rotate",
    description: "Rotate a key's secret value. Returns the new value once; old value is invalidated.",
    inputSchema: {
      type: "object",
      required: ["keyId"],
      properties: { keyId: { type: "string" } },
    },
  },
  {
    name: "key_update",
    description: "Update key metadata (name, expiresAt).",
    inputSchema: {
      type: "object",
      required: ["keyId"],
      properties: {
        keyId: { type: "string" },
        name: { type: "string" },
        expiresAt: { type: "string", description: "ISO 8601 expiry" },
      },
    },
  },
  {
    name: "key_delete",
    description: "Revoke/delete a key. Soft-delete -- can be restored by admin.",
    inputSchema: {
      type: "object",
      required: ["keyId"],
      properties: { keyId: { type: "string" } },
    },
  },
];

export const HOSTED_MCP_TOOL_NAMES = HOSTED_MCP_TOOLS.map((t) => t.name);
