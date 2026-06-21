import { liorgEnabled, liorgMe } from "./liorg-client";

export function studioOrgId(): string {
  return process.env.LIBREBASE_ORG_ID ?? "default";
}

export async function resolveStudioOrgId(): Promise<string> {
  if (!liorgEnabled()) {
    return studioOrgId();
  }
  if (process.env.LIBREBASE_ORG_ID) {
    return process.env.LIBREBASE_ORG_ID;
  }
  if (process.env.LIBREBASE_ORG_SESSION) {
    const me = await liorgMe();
    return me.activeOrgId;
  }
  return "default";
}
