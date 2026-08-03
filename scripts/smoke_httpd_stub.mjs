#!/usr/bin/env node
/** Smoke: gateway compose stub exists and lists core prefixes. */
import { readFileSync, existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const toml = path.join(root, "deploy", "edge", "librebase.httpd.toml");

if (!existsSync(toml)) {
  console.error("FAIL: missing", toml);
  process.exit(1);
}
const text = readFileSync(toml, "utf8");
for (const prefix of ["/rest/v1", "/v1/auth", "/storage/v1", "/functions/v1", "/realtime/v1"]) {
  if (!text.includes(prefix)) {
    console.error("FAIL: missing route prefix", prefix);
    process.exit(1);
  }
}
console.log(JSON.stringify({ ok: true, path: toml }));
