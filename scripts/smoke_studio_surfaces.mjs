#!/usr/bin/env node
/** Smoke: Studio operator surfaces exist on disk. */
import { existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "..",
  "data-studio-ui",
);
const need = [
  "app/setup/page.tsx",
  "app/login/page.tsx",
  "app/admin/page.tsx",
  "app/(studio)/(cloud)/logs/page.tsx",
  "app/api/admin/login/route.ts",
  "app/api/logs/route.ts",
];
const missing = need.filter((p) => !existsSync(path.join(root, p)));
if (missing.length) {
  console.error("FAIL: missing", missing);
  process.exit(1);
}
console.log(JSON.stringify({ ok: true, surfaces: need.length }));
