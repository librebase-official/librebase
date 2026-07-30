#!/usr/bin/env node
/**
 * @librebase/cli — thin orchestrator over Admin API + Studio.
 * Usage: librebase <command>
 */
import { spawn } from "node:child_process";
import { existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO =
  process.env.LIBREBASE_ROOT ??
  path.resolve(__dirname, "..", "..", "..");

const ADMIN_URL =
  process.env.LIBREBASE_ADMIN_URL ?? "http://127.0.0.1:54330";

function usage() {
  console.log(`librebase — Librebase product CLI

Commands:
  version              Print CLI version
  admin:health         GET Admin API /health
  admin:setup          POST /org/v1/setup (env: NAME EMAIL PASSWORD)
  start:admin          Start admin-api/scripts/admin_server.py
  start:studio         npm run dev in data-studio-ui
  matrix               Print capability matrix path / summary
  parity               Run Wave A scripts/parity_runner.py
  pins                 Print docs/li-dependency-pins.md path

Env:
  LIBREBASE_ROOT       Repo root (default: detect from package)
  LIBREBASE_ADMIN_URL  Admin API base (default ${ADMIN_URL})
  LIDB_ROOT            lidb checkout for parity / production runtime
`);
}

async function adminHealth() {
  const res = await fetch(`${ADMIN_URL}/health`);
  const text = await res.text();
  console.log(res.status, text);
  process.exit(res.ok ? 0 : 1);
}

async function adminSetup() {
  const name = process.env.NAME ?? "Local Org";
  const ownerEmail = process.env.EMAIL ?? "owner@localhost";
  const password = process.env.PASSWORD ?? "secret";
  const res = await fetch(`${ADMIN_URL}/org/v1/setup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, ownerEmail, password }),
  });
  const body = await res.text();
  console.log(res.status, body);
  process.exit(res.ok ? 0 : 1);
}

function startAdmin() {
  const script = path.join(REPO, "admin-api", "scripts", "admin_server.py");
  if (!existsSync(script)) {
    console.error("admin_server.py not found at", script);
    process.exit(1);
  }
  const python = process.env.PYTHON ?? (process.platform === "win32" ? "python" : "python3");
  const child = spawn(python, [script], {
    stdio: "inherit",
    env: {
      ...process.env,
      LIBREBASE_ADMIN_BIND: process.env.LIBREBASE_ADMIN_BIND ?? "127.0.0.1",
      LIBREBASE_ADMIN_PORT: process.env.LIBREBASE_ADMIN_PORT ?? "54330",
    },
  });
  child.on("exit", (code) => process.exit(code ?? 1));
}

function startStudio() {
  const cwd = path.join(REPO, "data-studio-ui");
  const child = spawn("npm", ["run", "dev"], {
    cwd,
    stdio: "inherit",
    shell: true,
    env: {
      ...process.env,
      LIBREBASE_ADMIN_URL: process.env.LIBREBASE_ADMIN_URL ?? ADMIN_URL,
    },
  });
  child.on("exit", (code) => process.exit(code ?? 1));
}

function matrix() {
  const p = path.join(REPO, "docs", "lidb-capability-matrix.md");
  console.log(existsSync(p) ? p : "docs/lidb-capability-matrix.md missing");
  console.log("See docs/parity-plan.md and docs/sdd/specs/supabase-parity/");
  const report = path.join(REPO, "tests", "parity", "last-report.json");
  if (existsSync(report)) {
    console.log("Last harness:", report);
  } else {
    console.log("Harness: not_run (librebase parity)");
  }
}

function pins() {
  const p = path.join(REPO, "docs", "li-dependency-pins.md");
  console.log(existsSync(p) ? p : "docs/li-dependency-pins.md missing");
}

function parity() {
  const runner = path.join(REPO, "scripts", "parity_runner.py");
  const child = spawn(process.env.PYTHON ?? "python", [runner], {
    cwd: REPO,
    stdio: "inherit",
    env: process.env,
  });
  child.on("exit", (code) => process.exit(code ?? 1));
}

const cmd = process.argv[2] ?? "help";
switch (cmd) {
  case "version":
  case "--version":
  case "-v":
    console.log("0.1.0");
    break;
  case "admin:health":
    await adminHealth();
    break;
  case "admin:setup":
    await adminSetup();
    break;
  case "start:admin":
    startAdmin();
    break;
  case "start:studio":
    startStudio();
    break;
  case "matrix":
    matrix();
    break;
  case "pins":
    pins();
    break;
  case "parity":
    parity();
    break;
  case "help":
  case "--help":
  case "-h":
  default:
    usage();
    if (cmd !== "help" && cmd !== "--help" && cmd !== "-h") process.exit(1);
}
