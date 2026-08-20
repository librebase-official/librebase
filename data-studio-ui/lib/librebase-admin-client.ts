/**
 * Librebase Admin API client — Studio operator auth + org/project metadata.
 * Product-branded management backend (not a linative lip package).
 *
 * Set LIBREBASE_ADMIN_URL to enable; optional LIBREBASE_ADMIN_SESSION bearer token.
 * LIBREBASE_ORG_URL / LIBREBASE_ORG_SESSION are deprecated aliases.
 */

import type {
  CreateHostInput,
  CreateInstanceInput,
  CreateProjectInput,
  Host,
  Instance,
  InstancePorts,
  InstanceStatus,
  Project,
} from "./types";

export interface AdminMe {
  user: { id: string; email: string };
  activeOrgId: string;
  role: string;
  edition: string;
  memberships: { orgId: string; role: string }[];
}

export interface AdminEntitlement {
  enabled: boolean;
  status: "allowed" | "denied" | "limited";
  code: number;
}

function adminUrlEnv(): string | undefined {
  return process.env.LIBREBASE_ADMIN_URL ?? process.env.LIBREBASE_ORG_URL;
}

function adminSessionEnv(): string | undefined {
  return (
    process.env.LIBREBASE_ADMIN_SESSION ?? process.env.LIBREBASE_ORG_SESSION
  );
}

const SESSION_COOKIE = "librebase_admin_session";
const REFRESH_COOKIE = "librebase_admin_refresh";

async function resolveAdminSession(): Promise<string | undefined> {
  const fromEnv = adminSessionEnv();
  if (fromEnv) return fromEnv;
  try {
    const { cookies } = await import("next/headers");
    const jar = await cookies();
    return jar.get(SESSION_COOKIE)?.value;
  } catch {
    return undefined;
  }
}

export function adminBaseUrl(): string {
  return adminUrlEnv()?.replace(/\/$/, "") ?? "http://127.0.0.1:54330";
}

export function adminApiEnabled(): boolean {
  return adminUrlEnv() !== undefined;
}

async function adminFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const token = await resolveAdminSession();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init?.headers as Record<string, string> | undefined),
  };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const res = await fetch(`${adminBaseUrl()}${path}`, { ...init, headers });
  if (!res.ok) {
    throw new Error(`librebase-admin ${path}: ${res.status} ${await res.text()}`);
  }
  if (res.status === 204) {
    return undefined as T;
  }
  return (await res.json()) as T;
}

function normalizeInstance(raw: Instance): Instance {
  return {
    ...raw,
    runtimeTarget: raw.runtimeTarget ?? "local",
    ports: raw.ports ?? { api: 54320, postgres: 54322 },
    status: (raw.status ?? "stopped") as InstanceStatus,
  };
}

export async function adminSetup(input: {
  name: string;
  ownerEmail: string;
  password: string;
  slug?: string;
}): Promise<{ orgId: string; token: string; refreshToken: string; mcpKey: string }> {
  return adminFetch("/org/v1/setup", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export async function adminLogin(
  email: string,
  password: string,
): Promise<{ token: string; orgId: string; refreshToken: string }> {
  return adminFetch("/org/v1/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export async function adminOAuthStart(
  provider: string,
  next = "/projects",
): Promise<string> {
  const res = await fetch(
    `${adminBaseUrl()}/org/v1/auth/oauth/start?provider=${encodeURIComponent(
      provider,
    )}&next=${encodeURIComponent(next)}`,
  );
  const data = (await res.json().catch(() => ({}))) as {
    url?: string;
    error?: string;
  };
  if (!res.ok || !data.url) {
    throw new Error(data.error ?? `oauth start ${res.status}`);
  }
  return data.url;
}

export async function adminOAuthCallback(
  provider: string,
  code: string,
): Promise<{ token: string; refreshToken: string; orgId: string; next: string }> {
  const res = await fetch(
    `${adminBaseUrl()}/org/v1/auth/oauth/callback?provider=${encodeURIComponent(
      provider,
    )}&code=${encodeURIComponent(code)}`,
  );
  const data = (await res.json().catch(() => ({}))) as {
    token?: string;
    refreshToken?: string;
    orgId?: string;
    next?: string;
    error?: string;
  };
  if (!res.ok || !data.token) {
    throw new Error(data.error ?? `oauth callback ${res.status}`);
  }
  return {
    token: data.token,
    refreshToken: data.refreshToken ?? "",
    orgId: data.orgId ?? "",
    next: data.next ?? "/projects",
  };
}

export async function adminRefresh(
  refreshToken: string,
): Promise<{ token: string; orgId: string; refreshToken: string }> {
  return adminFetch("/org/v1/auth/refresh", {
    method: "POST",
    body: JSON.stringify({ refreshToken }),
  });
}

export async function adminLogout(
  refreshToken: string,
): Promise<{ ok: boolean }> {
  return adminFetch("/org/v1/auth/logout", {
    method: "POST",
    body: JSON.stringify({ refreshToken }),
  });
}

export type McpKey = {
  id: string;
  orgId: string;
  createdAt: string;
  revoked: boolean;
  label?: string | null;
};

export async function adminListMcpKeys(orgId: string): Promise<McpKey[]> {
  return adminFetch(`/org/v1/orgs/${orgId}/mcp-keys`);
}

export async function adminIssueMcpKey(
  orgId: string,
  opts: { rotate?: boolean; label?: string } = {},
): Promise<{ mcpKey: string }> {
  return adminFetch(`/org/v1/orgs/${orgId}/mcp-keys`, {
    method: "POST",
    body: JSON.stringify({
      rotate: opts.rotate ?? false,
      label: opts.label,
    }),
  });
}

export async function adminRotateMcpKey(
  orgId: string,
  opts: { label?: string } = {},
): Promise<{ mcpKey: string }> {
  return adminFetch(`/org/v1/orgs/${orgId}/mcp-keys/rotate`, {
    method: "POST",
    body: JSON.stringify({ label: opts.label }),
  });
}

export async function adminChangePassword(
  currentPassword: string,
  newPassword: string,
): Promise<{ ok: boolean }> {
  return adminFetch("/org/v1/me/password", {
    method: "POST",
    body: JSON.stringify({ currentPassword, newPassword }),
  });
}

export async function adminMe(): Promise<AdminMe> {
  return adminFetch<AdminMe>("/org/v1/me");
}

export async function adminCreateOrg(input: { name: string; slug?: string }): Promise<{
  id: string;
  name: string;
  slug: string;
  edition: string;
}> {
  return adminFetch("/org/v1/orgs", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export async function adminSwitchOrg(orgId: string): Promise<{
  token: string;
  refreshToken: string;
  orgId: string;
  role: string;
  edition: string;
}> {
  return adminFetch("/org/v1/auth/switch-org", {
    method: "POST",
    body: JSON.stringify({ orgId }),
  });
}

export interface AdminInvite {
  token: string;
  email: string;
  role: string;
}

export interface AdminInvitePreview {
  orgId: string;
  orgName: string;
  email: string;
  role: string;
  expiresAt: string;
}

export async function adminCreateInvite(
  orgId: string,
  input: { email: string; role?: "developer" | "admin" | "owner" },
): Promise<AdminInvite> {
  return adminFetch(`/org/v1/orgs/${orgId}/invites`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export async function adminPreviewInvite(token: string): Promise<AdminInvitePreview> {
  return adminFetch(`/org/v1/invites/${token}`);
}

export async function adminAcceptInvite(token: string): Promise<{
  orgId: string;
  orgName: string;
  role: string;
  email: string;
}> {
  return adminFetch(`/org/v1/invites/${token}/accept`, {
    method: "POST",
    body: "{}",
  });
}

export async function adminListProjects(orgId: string): Promise<Project[]> {
  return adminFetch<Project[]>(`/org/v1/orgs/${orgId}/projects`);
}

export async function adminGetProject(
  orgId: string,
  projectId: string,
): Promise<Project | undefined> {
  try {
    return await adminFetch<Project>(
      `/org/v1/orgs/${orgId}/projects/${projectId}`,
    );
  } catch {
    return undefined;
  }
}

export async function adminCreateProject(
  orgId: string,
  input: Pick<Project, "name" | "instanceId" | "deploymentMode" | "region">,
): Promise<Project> {
  return adminFetch<Project>(`/org/v1/orgs/${orgId}/projects`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export async function adminListInstances(orgId: string): Promise<Instance[]> {
  const rows = await adminFetch<Instance[]>(
    `/org/v1/orgs/${orgId}/instances`,
  );
  return rows.map(normalizeInstance);
}

export async function adminGetInstance(
  orgId: string,
  instanceId: string,
): Promise<Instance | undefined> {
  try {
    const row = await adminFetch<Instance>(
      `/org/v1/orgs/${orgId}/instances/${instanceId}`,
    );
    return normalizeInstance(row);
  } catch {
    return undefined;
  }
}

export async function adminCreateInstance(
  orgId: string,
  input: CreateInstanceInput & {
    dataDir?: string;
    ports?: InstancePorts;
    status?: InstanceStatus;
    runtimeTarget?: string;
  },
): Promise<Instance> {
  const row = await adminFetch<Instance>(`/org/v1/orgs/${orgId}/instances`, {
    method: "POST",
    body: JSON.stringify({
      name: input.name,
      deploymentMode: input.deploymentMode ?? "dedicated",
      runtimeTarget: input.runtime ?? input.runtimeTarget ?? "local",
      dataDir: input.dataDir,
      ports: input.ports,
      status: input.status ?? "stopped",
      hostId: input.hostId,
      memLimitMb: input.memLimitMb,
    }),
  });
  return normalizeInstance(row);
}

export async function adminPatchInstance(
  orgId: string,
  instanceId: string,
  patch: Partial<
    Pick<
      Instance,
      | "status"
      | "dataDir"
      | "ports"
      | "k8sNamespace"
      | "k8sDegraded"
      | "k8sMessage"
    >
  >,
): Promise<Instance> {
  const row = await adminFetch<Instance>(
    `/org/v1/orgs/${orgId}/instances/${instanceId}`,
    { method: "PATCH", body: JSON.stringify(patch) },
  );
  return normalizeInstance(row);
}

export async function adminCheckEntitlement(
  orgId: string,
  featureKey: string,
): Promise<AdminEntitlement> {
  return adminFetch<AdminEntitlement>(
    `/org/v1/orgs/${orgId}/entitlements/${featureKey}`,
  );
}

export interface AdminMember {
  userId: string;
  email: string;
  role: string;
  createdAt: string;
}

export async function adminListMembers(orgId: string): Promise<AdminMember[]> {
  return adminFetch<AdminMember[]>(`/org/v1/orgs/${orgId}/members`);
}

export async function adminHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${adminBaseUrl()}/health`);
    return res.ok;
  } catch {
    return false;
  }
}

export async function adminListHosts(orgId: string): Promise<Host[]> {
  return adminFetch<Host[]>(`/org/v1/orgs/${orgId}/hosts`);
}

export async function adminGetHost(
  orgId: string,
  hostId: string,
): Promise<Host | undefined> {
  try {
    return await adminFetch<Host>(`/org/v1/orgs/${orgId}/hosts/${hostId}`);
  } catch {
    return undefined;
  }
}

export async function adminCreateHost(
  orgId: string,
  input: CreateHostInput,
): Promise<Host> {
  return adminFetch<Host>(`/org/v1/orgs/${orgId}/hosts`, {
    method: "POST",
    body: JSON.stringify({
      name: input.name,
      provider: input.provider ?? "linative-cloud",
      region: input.region ?? "local",
      memMb: input.memMb ?? 512,
    }),
  });
}

export { SESSION_COOKIE, REFRESH_COOKIE };
