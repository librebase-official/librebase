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
  activeOrgName?: string;
  role: string;
  edition: string;
  memberships: { orgId: string; role: string; name?: string }[];
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

const SESSION_MAX_AGE = 60 * 15;
const REFRESH_MAX_AGE = 60 * 60 * 24 * 30;

/** Auth cookies must only travel over TLS in production. */
const ADMIN_COOKIE_SECURE = process.env.NODE_ENV === "production";

function setSessionCookie(jar: { set(name: string, value: string, opts?: Record<string, unknown>): void }, token: string) {
  jar.set(SESSION_COOKIE, token, {
    httpOnly: true,
    sameSite: "lax",
    path: "/",
    maxAge: SESSION_MAX_AGE,
    secure: ADMIN_COOKIE_SECURE,
  });
}

function setRefreshCookie(jar: { set(name: string, value: string, opts?: Record<string, unknown>): void }, refreshToken: string) {
  jar.set(REFRESH_COOKIE, refreshToken, {
    httpOnly: true,
    sameSite: "lax",
    path: "/",
    maxAge: REFRESH_MAX_AGE,
    secure: ADMIN_COOKIE_SECURE,
  });
}

export function adminBaseUrl(): string {
  return adminUrlEnv()?.replace(/\/$/, "") ?? "http://127.0.0.1:54330";
}

export function adminApiEnabled(): boolean {
  return adminUrlEnv() !== undefined;
}

async function resolveAdminSession(): Promise<string | undefined> {
  const fromEnv = adminSessionEnv();
  if (fromEnv) return fromEnv;
  try {
    const { cookies } = await import("next/headers");
    const jar = await cookies();
    const access = jar.get(SESSION_COOKIE)?.value;
    if (access) return access;
    // Access token missing/expired: silently re-issue one from the long-lived
    // httpOnly refresh cookie so a new tab never forces a re-login.
    const refresh = jar.get(REFRESH_COOKIE)?.value;
    if (refresh) {
      const pair = await refreshAccessToken(refresh);
      if (pair) {
        // Backend rotates refresh tokens (old one is revoked after use). Persist
        // the new one into the browser's httpOnly cookie so that subsequent
        // expiries / new tabs keep refreshing instead of forcing a re-login.
        process.env.LIBREBASE_ADMIN_SESSION = pair.token;
        setSessionCookie(jar, pair.token);
        setRefreshCookie(jar, pair.refreshToken);
        return pair.token;
      }
    }
  } catch {
    return undefined;
  }
  return undefined;
}

let refreshing: Promise<SessionPair | null> | null = null;
interface SessionPair {
  token: string;
  refreshToken: string;
}
async function refreshAccessToken(refreshToken: string): Promise<SessionPair | null> {
  if (refreshing) return refreshing;
  refreshing = (async () => {
    try {
      const res = await fetch(`${adminBaseUrl()}/org/v1/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refreshToken }),
      });
      if (!res.ok) return null;
      const data = (await res.json()) as { token?: string; refreshToken?: string };
      if (!data.token || !data.refreshToken) return null;
      return { token: data.token, refreshToken: data.refreshToken };
    } catch {
      return null;
    } finally {
      refreshing = null;
    }
  })();
  return refreshing;
}

type FetchInit = Omit<RequestInit, "headers"> & {
  headers?: Record<string, string>;
  _retry?: boolean;
};

export class AdminApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly body: unknown,
  ) {
    super(message);
    this.name = "AdminApiError";
  }
}

/** JSON error payload + HTTP status for Studio API routes that wrap admin-api. */
export function adminErrorPayload(
  error: unknown,
  fallback = "Request failed",
): { error: string; status: number } {
  if (error instanceof AdminApiError) {
    const body = error.body;
    const msg =
      typeof body === "object" && body !== null && "error" in body
        ? String((body as { error: unknown }).error)
        : error.message;
    return { error: msg, status: error.status || 500 };
  }
  return {
    error: error instanceof Error ? error.message : fallback,
    status: 500,
  };
}

async function adminFetch<T>(path: string, init?: FetchInit): Promise<T> {
  const token = await resolveAdminSession();
  const baseHeaders: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init?.headers as Record<string, string> | undefined),
  };
  if (token) baseHeaders.Authorization = `Bearer ${token}`;
  const common: RequestInit = { ...init, headers: baseHeaders };
  let res = await fetch(`${adminBaseUrl()}${path}`, common);
  if (!res.ok) {
    // Access token may have just expired: silently refresh from the refresh cookie
    // (once) and retry, so opening the console in a new tab never forces a re-login.
    if (res.status === 401 && !init?._retry) {
      const refreshed = await resolveAdminSession();
      if (refreshed) {
        res = await fetch(`${adminBaseUrl()}${path}`, {
          ...common,
          headers: { ...baseHeaders, Authorization: `Bearer ${refreshed}` },
        });
      }
    }
    if (!res.ok) {
      const text = await res.text().catch(() => "");
      let parsed: unknown = text;
      try {
        parsed = text ? JSON.parse(text) : {};
      } catch {
        parsed = text;
      }
      const errMsg =
        typeof parsed === "object" && parsed !== null && "error" in parsed
          ? String((parsed as { error: unknown }).error)
          : text;
      throw new AdminApiError(
        `librebase-admin ${path}: ${res.status} ${errMsg}`,
        res.status,
        parsed,
      );
    }
  }
  if (res.status === 204) return undefined as T;
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
};

export type McpDeviceView = {
  userCode: string;
  clientName: string;
  expiresAt: string;
  status: "pending" | "approved" | "denied" | "expired" | string;
  memberships: { orgId: string; role: string; name?: string }[];
  activeOrgId?: string;
};

export type McpDeviceStart = {
  deviceCode: string;
  userCode: string;
  verificationUri: string;
  verificationUriComplete: string;
  expiresIn: number;
  interval: number;
};

export type McpDeviceToken = {
  accessToken?: string;
  tokenType?: string;
  orgId?: string;
  role?: string;
  expiresIn?: number;
  error?: string;
  interval?: number;
};

async function adminPublicFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${adminBaseUrl()}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers as Record<string, string> | undefined),
    },
    cache: "no-store",
  });
  const text = await res.text().catch(() => "");
  let parsed: unknown = text;
  try {
    parsed = text ? JSON.parse(text) : {};
  } catch {
    parsed = text;
  }
  if (!res.ok) {
    throw new AdminApiError(
      `librebase-admin ${path}: ${res.status}`,
      res.status,
      parsed,
    );
  }
  return parsed as T;
}

export async function adminMcpDeviceStart(input?: {
  clientName?: string;
}): Promise<McpDeviceStart> {
  return adminPublicFetch("/org/v1/mcp/device/start", {
    method: "POST",
    body: JSON.stringify(input ?? {}),
  });
}

export async function adminMcpDeviceToken(deviceCode: string): Promise<McpDeviceToken> {
  return adminPublicFetch("/org/v1/mcp/device/token", {
    method: "POST",
    body: JSON.stringify({ deviceCode }),
  });
}

export async function adminGetMcpDevice(userCode: string): Promise<McpDeviceView> {
  return adminFetch(`/org/v1/mcp/device/${encodeURIComponent(userCode)}`);
}

export async function adminApproveMcpDevice(
  userCode: string,
  orgId?: string,
  fullAgentMode?: boolean,
  scope?: "user" | "project",
  projectId?: string,
): Promise<{
  ok: boolean;
  status: string;
  orgId?: string;
  role?: string;
  scope?: string;
  projectId?: string;
}> {
  const body: Record<string, unknown> = {};
  if (orgId) body.orgId = orgId;
  if (fullAgentMode) body.fullAgentMode = true;
  if (scope) body.scope = scope;
  if (projectId) body.projectId = projectId;
  return adminFetch(`/org/v1/mcp/device/${encodeURIComponent(userCode)}/approve`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function adminDenyMcpDevice(
  userCode: string,
): Promise<{ ok: boolean; status: string }> {
  return adminFetch(`/org/v1/mcp/device/${encodeURIComponent(userCode)}/deny`, {
    method: "POST",
    body: "{}",
  });
}

export type ProjectAuthProvider = {
  provider: "github" | "google" | string;
  clientId: string;
  redirectUris: string[];
  enabled: boolean;
  updatedAt?: string;
};

export async function adminListProjectProviders(
  orgId: string,
  projectId: string,
): Promise<ProjectAuthProvider[]> {
  return adminFetch(`/org/v1/orgs/${orgId}/projects/${projectId}/providers`);
}

export async function adminUpsertProjectProvider(
  orgId: string,
  projectId: string,
  input: {
    provider: string;
    clientId: string;
    clientSecret?: string;
    redirectUris: string[];
    enabled?: boolean;
  },
): Promise<ProjectAuthProvider> {
  return adminFetch(`/org/v1/orgs/${orgId}/projects/${projectId}/providers`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export async function adminListMcpKeys(orgId: string): Promise<McpKey[]> {
  return adminFetch(`/org/v1/orgs/${orgId}/mcp-keys`);
}

export async function adminRotateMcpKey(
  orgId: string,
): Promise<{ mcpKey: string }> {
  return adminFetch(`/org/v1/orgs/${orgId}/mcp-keys/rotate`, {
    method: "POST",
    body: "{}",
  });
}

// --- Scoped KMS keys (docs/kms-agent-keys-vision.md) ---

export type KmsKey = {
  keyId: string;
  scope: "org" | "project" | "cross_org";
  projectId: string | null;
  orgId: string | null;
  ownerUser: string | null;
  name: string;
  kind: "secret" | "keypair";
  managed: "user" | "platform";
  version: number;
  publicKey: string | null;
  rateLimit: number;
  expiresAt: string | null;
  createdAt: string;
  updatedAt: string;
  rotatedAt: string | null;
};

export type KmsKeyInput = {
  name: string;
  plaintext: string;
  scope?: "org" | "project";
  projectId?: string;
  rateLimit?: number;
  expiresAt?: string;
};

export async function adminListOrgKeys(
  orgId: string,
  scope?: "org" | "project",
  projectId?: string,
): Promise<{ keys: KmsKey[] }> {
  const qs = new URLSearchParams();
  if (scope) qs.set("scope", scope);
  if (projectId) qs.set("projectId", projectId);
  const suffix = qs.toString() ? `?${qs.toString()}` : "";
  return adminFetch(`/org/v1/orgs/${orgId}/keys${suffix}`);
}

export async function adminCreateOrgKey(
  orgId: string,
  input: KmsKeyInput,
): Promise<KmsKey> {
  return adminFetch(`/org/v1/orgs/${orgId}/keys`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export async function adminListMyKeys(): Promise<{ keys: KmsKey[] }> {
  return adminFetch(`/org/v1/me/keys`);
}

export async function adminCreateMyKey(input: KmsKeyInput): Promise<KmsKey> {
  return adminFetch(`/org/v1/me/keys`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export async function adminGetKey(keyId: string): Promise<KmsKey> {
  return adminFetch(`/org/v1/keys/${keyId}`);
}

export async function adminDecryptKey(
  keyId: string,
): Promise<{ data: string }> {
  return adminFetch(`/org/v1/keys/${keyId}/decrypt`, {
    method: "POST",
    body: "{}",
  });
}

export async function adminRotateKey(
  keyId: string,
  plaintext?: string,
): Promise<KmsKey> {
  return adminFetch(`/org/v1/keys/${keyId}/rotate`, {
    method: "POST",
    body: JSON.stringify(plaintext ? { plaintext } : {}),
  });
}

export async function adminUpdateKey(
  keyId: string,
  input: { rateLimit?: number; expiresAt?: string | null },
): Promise<KmsKey> {
  return adminFetch(`/org/v1/keys/${keyId}`, {
    method: "PATCH",
    body: JSON.stringify(input),
  });
}

export async function adminDeleteKey(keyId: string): Promise<{ ok: boolean }> {
  return adminFetch(`/org/v1/keys/${keyId}`, { method: "DELETE" });
}

export async function adminListApps(
  orgId: string,
): Promise<{ apps: { id: string; name: string; projectId: string | null; createdAt: string; revoked: boolean }[] }> {
  return adminFetch(`/org/v1/orgs/${orgId}/apps`);
}

export async function adminCreateApp(
  orgId: string,
  input: { name: string; projectId?: string },
): Promise<{ appKey: string; id: string; name: string }> {
  return adminFetch(`/org/v1/orgs/${orgId}/apps`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export async function adminRotateInstanceKeys(
  orgId: string,
  instanceId: string,
): Promise<{ rotated: string[] }> {
  return adminFetch(
    `/org/v1/orgs/${orgId}/instances/${instanceId}/keys/rotate`,
    { method: "POST", body: "{}" },
  );
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

export interface AdminBilling {
  orgId: string;
  plan: string;
  edition: string;
  price: number;
  instanceLimit: number;
  instanceCount: number;
  stripeConfigured: boolean;
  stripeStatus?: string | null;
  stripePriceId?: string | null;
}

export async function adminGetBilling(orgId: string): Promise<AdminBilling> {
  return adminFetch<AdminBilling>(`/org/v1/orgs/${orgId}/billing`);
}

export async function adminCreateBillingSession(
  orgId: string,
  plan: "starter" | "pro" | "scale",
): Promise<{ url: string; plan: string }> {
  return adminFetch(`/org/v1/orgs/${orgId}/billing/session`, {
    method: "POST",
    body: JSON.stringify({ plan }),
  });
}

export async function adminCreateBillingPortal(orgId: string): Promise<{ url: string }> {
  return adminFetch(`/org/v1/orgs/${orgId}/billing/portal`, {
    method: "POST",
    body: "{}",
  });
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

/**
 * True when an admin-api failure means "the resource does not exist" as
 * opposed to "we could not verify right now" (401/403/5xx/network). Callers
 * must not render a 404 page for the latter — that turns a dead session or a
 * transient backend hiccup into a dead-end "page not found" for the user.
 */
function isGoneError(error: unknown): boolean {
  return error instanceof AdminApiError && (error.status === 404 || error.status === 410);
}

export async function adminGetProject(
  orgId: string,
  projectId: string,
): Promise<Project | undefined> {
  try {
    return await adminFetch<Project>(
      `/org/v1/orgs/${orgId}/projects/${projectId}`,
    );
  } catch (error) {
    if (isGoneError(error)) return undefined;
    throw error;
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

export async function adminPatchProject(
  orgId: string,
  projectId: string,
  patch: { instanceId?: string; name?: string },
): Promise<Project> {
  return adminFetch<Project>(`/org/v1/orgs/${orgId}/projects/${projectId}`, {
    method: "PATCH",
    body: JSON.stringify(patch),
  });
}

export async function adminDeleteProject(
  orgId: string,
  projectId: string,
): Promise<{ ok: boolean; projectsDeleted?: number }> {
  return adminFetch<{ ok: boolean; projectsDeleted?: number }>(
    `/org/v1/orgs/${orgId}/projects/${projectId}`,
    { method: "DELETE" },
  );
}

export async function adminUpdateOrg(
  orgId: string,
  patch: { name: string },
): Promise<{ id: string; name: string; slug: string }> {
  return adminFetch<{ id: string; name: string; slug: string }>(
    `/org/v1/orgs/${orgId}`,
    { method: "PATCH", body: JSON.stringify(patch) },
  );
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
  } catch (error) {
    if (isGoneError(error)) return undefined;
    throw error;
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

export async function adminDeleteInstance(
  orgId: string,
  instanceId: string,
): Promise<{ ok: boolean; projectsDeleted?: number }> {
  return adminFetch<{ ok: boolean; projectsDeleted?: number }>(
    `/org/v1/orgs/${orgId}/instances/${instanceId}`,
    { method: "DELETE" },
  );
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
  } catch (error) {
    if (isGoneError(error)) return undefined;
    throw error;
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

export async function adminDeleteHost(
  orgId: string,
  hostId: string,
): Promise<{ ok: boolean; instancesDeleted?: number }> {
  return adminFetch<{ ok: boolean; instancesDeleted?: number }>(
    `/org/v1/orgs/${orgId}/hosts/${hostId}`,
    { method: "DELETE" },
  );
}

export { SESSION_COOKIE, REFRESH_COOKIE, ADMIN_COOKIE_SECURE };
