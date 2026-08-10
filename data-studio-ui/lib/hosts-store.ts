import { resolveStudioOrgId } from "./org-context";
import {
  adminApiEnabled,
  adminCreateHost,
  adminListHosts,
} from "./librebase-admin-client";
import type { CreateHostInput, Host } from "./types";

export function listHostsSync(_orgId?: string): Host[] {
  return [];
}

export async function listHostsAsync(orgId?: string): Promise<Host[]> {
  const resolvedOrg = orgId ?? (await resolveStudioOrgId());
  if (!adminApiEnabled()) {
    return listHostsSync(resolvedOrg);
  }
  return adminListHosts(resolvedOrg);
}

export async function createHostAsync(input: CreateHostInput): Promise<Host> {
  const orgId = input.orgId ?? (await resolveStudioOrgId());
  if (!adminApiEnabled()) {
    throw new Error("hosts require LIBREBASE_ADMIN_URL (control plane)");
  }
  return adminCreateHost(orgId, input);
}

/** Host-aware port block allocation so instances on one VM share its port space. */
export function hostPortBlock(index: number): { api: number; postgres: number } {
  return { api: 54320 + index * 10, postgres: 54322 + index * 10 };
}
