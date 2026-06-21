/**
 * liorg control-plane HTTP client (Librebase Studio operator auth + org metadata).
 * Set LIBREBASE_ORG_URL (default http://127.0.0.1:54330).
 */

import type {
  CreateInstanceInput,
  CreateProjectInput,
  Instance,
  Project,
} from "./types";

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
  return (await res.json()) as T;
}

export async function liorgListProjects(orgId: string): Promise<Project[]> {
  return liorgFetch<Project[]>(`/org/v1/orgs/${orgId}/projects`);
}

export async function liorgCreateProject(
  orgId: string,
  input: CreateProjectInput,
): Promise<Project> {
  return liorgFetch<Project>(`/org/v1/orgs/${orgId}/projects`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export async function liorgListInstances(orgId: string): Promise<Instance[]> {
  return liorgFetch<Instance[]>(`/org/v1/orgs/${orgId}/instances`);
}

export async function liorgCreateInstance(
  orgId: string,
  input: CreateInstanceInput,
): Promise<Instance> {
  return liorgFetch<Instance>(`/org/v1/orgs/${orgId}/instances`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export async function liorgCheckEntitlement(
  orgId: string,
  featureKey: string,
): Promise<boolean> {
  const res = await liorgFetch<{ enabled: boolean }>(
    `/org/v1/orgs/${orgId}/entitlements/${featureKey}`,
  );
  return res.enabled;
}

export async function liorgHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${liorgBaseUrl()}/health`);
    return res.ok;
  } catch {
    return false;
  }
}
