import {
  adminApiEnabled,
  adminCheckEntitlement,
  type AdminEntitlement,
} from "./librebase-admin-client";
import { studioOrgId } from "./org-context";

export class EntitlementError extends Error {
  constructor(
    message: string,
    readonly featureKey: string,
    readonly entitlement: AdminEntitlement,
  ) {
    super(message);
    this.name = "EntitlementError";
  }
}

export async function requireEntitlement(
  featureKey: string,
  orgId = studioOrgId(),
): Promise<AdminEntitlement> {
  if (!adminApiEnabled()) {
    return { enabled: true, status: "allowed", code: 1 };
  }
  const entitlement = await adminCheckEntitlement(orgId, featureKey);
  if (!entitlement.enabled) {
    throw new EntitlementError(
      `Feature "${featureKey}" is not enabled for this organization`,
      featureKey,
      entitlement,
    );
  }
  return entitlement;
}

export async function checkEntitlement(
  featureKey: string,
  orgId = studioOrgId(),
): Promise<boolean> {
  if (!adminApiEnabled()) {
    return true;
  }
  const entitlement = await adminCheckEntitlement(orgId, featureKey);
  return entitlement.enabled;
}
