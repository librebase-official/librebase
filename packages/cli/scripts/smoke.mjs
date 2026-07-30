#!/usr/bin/env node
/** CLI smoke — version + help exit 0. */
import { spawnSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const cli = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "src", "index.js");

function run(args) {
  const r = spawnSync(process.execPath, [cli, ...args], { encoding: "utf8" });
  if (r.status !== 0) {
    console.error("FAIL", args, r.stderr || r.stdout);
    process.exit(1);
  }
  return r.stdout;
}

const ver = run(["version"]).trim();
if (!/^\d+\.\d+\.\d+/.test(ver)) {
  console.error("FAIL: unexpected version", ver);
  process.exit(1);
}
run(["--help"]);
console.log(JSON.stringify({ ok: true, version: ver }));
