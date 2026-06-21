/**
 * liorg control-plane HTTP client (Librebase Studio operator auth + org metadata).
 * Set LIBREBASE_ORG_URL to enable; optional LIBREBASE_ORG_SESSION bearer token.
 */

import type {
  CreateInstanceInput,
  CreateProjectInput,
  Instance,
  InstancePorts,
  InstanceStatus,
  Project,
} from "./types";

export interface LiorgMe {
  user: { id: string; email: string };
  activeOrgId: string;
  role: string;
  edition: string;
  memberships: { orgId: string; role: string }[];
}

export interface LiorgEntitlement {
  enabled: boolean;
  status: "allowed" | "denied" | "limited";
  code: number;
}

export function liorgBaseUrl(): string {
  return (
    process.env.LIBREBASE_ORG_URL?.replace(/\/$/, "") ??
    "http://127.0.0.1:54330"
  );
}

export function liorgEnabled(): boolean {
  return process.env.LIBREBASE_ORG_URL !== undefined;
}

async function liorgFetch<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const token = process.env.LIBREBASE_ORG_SESSION;
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init?.headers as Record<string, string> | undefined),
  };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const res = await fetch(`${liorgBaseUrl()}${path}`, { ...init, headers });
  if (!res.ok) {
    throw new Error(`liorg ${path}: ${res.status} ${await res.text()}`);
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

export async function liorgSetup(input: {
  name: string;
  ownerEmail: string;
  password: string;
  slug?: string;
}): Promise<{ orgId: string; token: string }> {
  return liorgFetch("/org/v1/setup", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export async function liorgLogin(
  email: string,
  password: string,
): Promise<{ token: string; orgId: string }> {
  return liorgFetch("/org/v1/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export async function liorgMe(): Promise<LiorgMe> {
  return liorgFetch<LiorgMe>("/org/v1/me");
}

export async function liorgListProjects(orgId: string): Promise<Project[]> {
  return liorgFetch<Project[]>(`/org/v1/orgs/${orgId}/projects`);
}

export async function liorgGetProject(
  orgId: string,
  projectId: string,
): Promise<Project | undefined> {
  try {
    return await liorgFetch<Project>(
      `/org/v1/orgs/${orgId}/projects/${projectId}`,
    );
  } catch {
    return undefined;
  }
}

export async function liorgCreateProject(
  orgId: string,
  input: Pick<
    Project,
    "name" | "instanceId" | "deploymentMode" | "region"
  >,
): Promise<Project> {
  return liorgFetch<Project>(`/org/v1/orgs/${orgId}/projects`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export async function liorgListInstances(orgId: string): Promise<Instance[]> {
  const rows = await liorgFetch<Instance[]>(
    `/org/v1/orgs/${orgId}/instances`,
  );
  return rows.map(normalizeInstance);
}

export async function liorgGetInstance(
  orgId: string,
  instanceId: string,
): Promise<Instance | undefined> {
  try {
    const row = await liorgFetch<Instance>(
      `/org/v1/orgs/${orgId}/instances/${instanceId}`,
    );
    return normalizeInstance(row);
  } catch {
    return undefined;
  }
}

export async function liorgCreateInstance(
  orgId: string,
  input: CreateInstanceInput & {
    dataDir?: string;
    ports?: InstancePorts;
    status?: InstanceStatus;
    runtimeTarget?: string;
  },
): Promise<Instance> {
  const row = await liorgFetch<Instance>(`/org/v1/orgs/${orgId}/instances`, {
    method: "POST",
    body: JSON.stringify({
      name: input.name,
      deploymentMode: input.deploymentMode ?? "dedicated",
      runtimeTarget: input.runtime ?? input.runtimeTarget ?? "local",
      dataDir: input.dataDir,
      ports: input.ports,
      status: input.status ?? "stopped",
    }),
  });
  return normalizeInstance(row);
}

export async function liorgPatchInstance(
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
  const row = await liorgFetch<Instance>(
    `/org/v1/orgs/${orgId}/instances/${instanceId}`,
    { method: "PATCH", body: JSON.stringify(patch) },
  );
  return normalizeInstance(row);
}

export async function liorgCheckEntitlement(
  orgId: string,
  featureKey: string,
): Promise<LiorgEntitlement> {
  return liorgFetch<LiorgEntitlement>(
    `/org/v1/orgs/${orgId}/entitlements/${featureKey}`,
  );
}

export async function liorgHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${liorgBaseUrl()}/health`);
    return res.ok;
  } catch {
    return false;
  }
}
