/**
 * CLI smoke — version and --help exit 0 with expected output.
 */
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const cli = path.resolve(__dirname, "..", "src", "index.js");

function run(args) {
  return spawnSync(process.execPath, [cli, ...args], {
    encoding: "utf8",
    env: process.env,
  });
}

const ver = run(["version"]);
assert.equal(ver.status, 0, `version exit ${ver.status}: ${ver.stderr}`);
assert.match(ver.stdout, /0\.1\.0/);

const help = run(["--help"]);
assert.equal(help.status, 0, `--help exit ${help.status}: ${help.stderr}`);
assert.match(help.stdout, /librebase/i);
assert.match(help.stdout, /Commands:/);

const matrix = run(["matrix"]);
assert.equal(matrix.status, 0, `matrix exit ${matrix.status}: ${matrix.stderr}`);

console.log("cli smoke ok");
