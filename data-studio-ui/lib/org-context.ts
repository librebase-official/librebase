import { adminApiEnabled, adminMe } from "./librebase-admin-client";

export function studioOrgId(): string {
  return process.env.LIBREBASE_ORG_ID ?? "default";
}

export async function resolveStudioOrgId(): Promise<string> {
  if (!adminApiEnabled()) {
    return studioOrgId();
  }
  if (process.env.LIBREBASE_ORG_ID) {
    return process.env.LIBREBASE_ORG_ID;
  }
  try {
    const me = await adminMe();
    return me.activeOrgId;
  } catch {
    return "default";
  }
}
