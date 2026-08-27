/**
 * Client for the admin-dashboard API (internal, behind LIBREBASE_ADMIN_DASHBOARD_TOKEN).
 *
 * Server-side only — this module reads env vars at runtime and should never
 * be imported from client components.
 */

const ADMIN_API_URL =
  process.env.ADMIN_API_URL || "http://127.0.0.1:54341";
const ADMIN_TOKEN =
  process.env.LIBREBASE_ADMIN_DASHBOARD_TOKEN || "";

async function adminFetch<T = unknown>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const url = `${ADMIN_API_URL}${path}`;
  try {
    const res = await fetch(url, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${ADMIN_TOKEN}`,
        ...init?.headers,
      },
      cache: "no-store",
    });
    if (!res.ok) {
      const body = await res.text();
      throw new Error(`Admin API ${res.status}: ${body}`);
    }
    return res.json() as Promise<T>;
  } catch (err) {
    console.error(`[admin-client] fetch ${url} failed:`, err);
    throw err;
  }
}

export interface Overview {
  orgCount: number;
  userCount: number;
  instanceCount: number;
  hostCount: number;
  projectCount: number;
  planDistribution: Record<string, number>;
  instanceByState: Record<string, number>;
  hostByState: Record<string, number>;
}

export interface OrgRow {
  id: string;
  name: string;
  slug: string;
  edition: string;
  plan: string;
  stripe_status: string;
  created_at: string;
  member_count: number;
  instance_count: number;
  project_count: number;
}

export interface UserRow {
  id: string;
  email: string;
  mfa_enabled: number;
  created_at: string;
  org_names: string;
}

export interface HostRow {
  id: string;
  name: string;
  provider: string;
  server_id: string | null;
  ip: string;
  status: string;
  region: string;
  mem_mb: number;
  org_id: string;
  created_at: string;
  org_name: string;
  instance_count: number;
}

export interface InstanceRow {
  id: string;
  name: string;
  status: string;
  host_id: string;
  org_id: string;
  mem_limit_mb: number;
  created_at: string;
  org_name: string;
  host_name: string;
  host_ip: string;
}

export interface HetznerServer {
  id: number;
  name: string;
  status: string;
  serverType: string;
  ip: string;
  region: string;
  monthlyCost: number;
  createdAt: string;
}

export interface HetznerCosts {
  servers: HetznerServer[];
  pricing: Record<string, number>;
  totalMonthly: number;
}

export const getOverview = () => adminFetch<Overview>("/admin/v1/overview");
export const getOrgs = () => adminFetch<OrgRow[]>("/admin/v1/orgs");
export const getUsers = () => adminFetch<UserRow[]>("/admin/v1/users");
export const getHosts = () => adminFetch<HostRow[]>("/admin/v1/hosts");
export const getInstances = () =>
  adminFetch<InstanceRow[]>("/admin/v1/instances");
export const getHetznerCosts = () =>
  adminFetch<HetznerCosts>("/admin/v1/hetzner/costs");

export const stopHost = (hostId: string) =>
  adminFetch<{ ok: boolean; status: string }>(
    `/admin/v1/hosts/${hostId}/stop`,
    { method: "POST", body: "{}" },
  );

export const startHost = (hostId: string) =>
  adminFetch<{ ok: boolean; status: string }>(
    `/admin/v1/hosts/${hostId}/start`,
    { method: "POST", body: "{}" },
  );

export const deleteHost = (hostId: string) =>
  adminFetch<{ ok: boolean }>(`/admin/v1/hosts/${hostId}`, {
    method: "DELETE",
  });

export interface McpUsage {
  totalCalls: number;
  callsToday: number;
  byOrg: { org_id: string; cnt: number; last_call: string }[];
  byTool: { tool_name: string; cnt: number; avg_ms: number; errors: number }[];
  hourly: { hour: string; cnt: number }[];
}

export const getMcpUsage = () => adminFetch<McpUsage>("/admin/v1/mcp/usage");

export function adminEnabled(): boolean {
  return !!ADMIN_TOKEN;
}
