import {
  liorgCheckEntitlement,
  liorgEnabled,
  type LiorgEntitlement,
} from "./liorg-client";
import { studioOrgId } from "./org-context";

export class EntitlementError extends Error {
  constructor(
    message: string,
    readonly featureKey: string,
    readonly entitlement: LiorgEntitlement,
  ) {
    super(message);
    this.name = "EntitlementError";
  }
}

export async function requireEntitlement(
  featureKey: string,
  orgId = studioOrgId(),
): Promise<LiorgEntitlement> {
  if (!liorgEnabled()) {
    return { enabled: true, status: "allowed", code: 1 };
  }
  const entitlement = await liorgCheckEntitlement(orgId, featureKey);
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
  if (!liorgEnabled()) {
    return true;
  }
  const entitlement = await liorgCheckEntitlement(orgId, featureKey);
  return entitlement.enabled;
}
