import fs from "node:fs";
import path from "node:path";

/**
 * Returns true when pathname maps to a static App Router page or route handler
 * under data-studio-ui/app (no production fetch).
 */
export function appRouterPathExists(appDir: string, pathname: string): boolean {
  const normalized = pathname === "" ? "/" : pathname.startsWith("/") ? pathname : `/${pathname}`;
  if (normalized === "/") {
    return fs.existsSync(path.join(appDir, "page.tsx"));
  }

  const segments = normalized.split("/").filter(Boolean);
  let dir = appDir;
  for (const segment of segments) {
    dir = path.join(dir, segment);
  }

  return (
    fs.existsSync(path.join(dir, "page.tsx")) ||
    fs.existsSync(path.join(dir, "route.ts"))
  );
}

/** Extract site-origin paths referenced in llms.txt body (e.g. https://app.librebase.xyz/for-agents). */
export function extractSitePathsFromLlmsBody(body: string, siteOrigin: string): string[] {
  const origin = siteOrigin.replace(/\/$/, "");
  const escaped = origin.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const re = new RegExp(`${escaped}(/[^\\s)\\]"']*)?`, "g");
  const paths = new Set<string>();
  for (const match of body.matchAll(re)) {
    paths.add(match[1] && match[1].length > 0 ? match[1] : "/");
  }
  return [...paths].sort();
}
