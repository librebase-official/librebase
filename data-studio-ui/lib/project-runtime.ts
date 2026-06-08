import { spawnSync } from "node:child_process";
import net from "node:net";
import path from "node:path";
import { getInstance, updateInstanceStatus } from "./instances-store";
import { getProject } from "./projects-store";
import type { DbProbeResult, Instance, Project } from "./types";

const REPO_ROOT = path.resolve(process.cwd(), "..");
const LIDB_ENGINE = path.join(REPO_ROOT, "scripts", "lidb_engine.py");

function isPortOpen(host: string, port: number, timeoutMs = 500): Promise<boolean> {
  return new Promise((resolve) => {
    const socket = net.createConnection({ host, port });
    const done = (open: boolean) => {
      socket.destroy();
      resolve(open);
    };
    socket.setTimeout(timeoutMs);
    socket.on("connect", () => done(true));
    socket.on("timeout", () => done(false));
    socket.on("error", () => done(false));
  });
}

function runEngine(
  command: string,
  instance: Instance,
): { ok: boolean; payload: Record<string, unknown>; stderr: string } {
  const python = process.env.PYTHON ?? "python";
  const result = spawnSync(
    python,
    [
      LIDB_ENGINE,
      command,
      "--data-dir",
      instance.dataDir,
      "--api-port",
      String(instance.ports.api),
      "--postgres-port",
      String(instance.ports.postgres),
    ],
    {
      encoding: "utf8",
      env: {
        ...process.env,
        LI_DATA_DIR: instance.dataDir,
      },
    },
  );

  let payload: Record<string, unknown> = {};
  const stdout = (result.stdout ?? "").trim();
  if (stdout) {
    try {
      payload = JSON.parse(stdout) as Record<string, unknown>;
    } catch {
      payload = { raw: stdout };
    }
  }

  return {
    ok: result.status === 0,
    payload,
    stderr: (result.stderr ?? "").trim(),
  };
}

export function getApiUrl(instance: Instance): string {
  return `http://127.0.0.1:${instance.ports.api}`;
}

export function getPostgresUrl(instance: Instance): string {
  return `postgresql://127.0.0.1:${instance.ports.postgres}/librebase`;
}

export function getProjectUrls(project: Project): {
  apiUrl: string;
  postgresUrl: string;
} | null {
  const instance = getInstance(project.instanceId);
  if (!instance) return null;
  return {
    apiUrl: getApiUrl(instance),
    postgresUrl: getPostgresUrl(instance),
  };
}

export async function probeInstanceDb(instance: Instance): Promise<DbProbeResult> {
  const engine = runEngine("status", instance);
  const engineStatus = String(engine.payload.status ?? "unknown");
  const degraded = Boolean(engine.payload.degraded);
  const message = String(
    engine.payload.message ??
      engine.stderr ??
      (degraded ? "Runtime unavailable (degraded mode)" : "Status probe complete"),
  );

  const portOpen = await isPortOpen("127.0.0.1", instance.ports.api);

  let status = instance.status;
  if (engine.ok && engineStatus === "running" && portOpen) {
    status = "running";
  } else if (engineStatus === "starting") {
    status = "starting";
  } else if (degraded || !engine.ok) {
    status = "stopped";
  } else if (!portOpen) {
    status = "stopped";
  }

  updateInstanceStatus(instance.id, status);

  return {
    reachable: portOpen && status === "running",
    status,
    degraded: degraded || !engine.ok,
    message,
  };
}

export async function probeProjectDb(projectId: string): Promise<DbProbeResult> {
  const project = getProject(projectId);
  if (!project) {
    return {
      reachable: false,
      status: "unknown",
      degraded: true,
      message: `Project not found: ${projectId}`,
    };
  }

  const instance = getInstance(project.instanceId);
  if (!instance) {
    return {
      reachable: false,
      status: "unknown",
      degraded: true,
      message: `Instance not found for project: ${projectId}`,
    };
  }

  return probeInstanceDb(instance);
}

export async function launchProjectDb(projectId: string): Promise<{
  ok: boolean;
  probe: DbProbeResult;
  launchMessage: string;
}> {
  // TODO: entitlement check — block launch without active Studio/lidb plan or license.
  const project = getProject(projectId);
  if (!project) {
    return {
      ok: false,
      probe: {
        reachable: false,
        status: "unknown",
        degraded: true,
        message: `Project not found: ${projectId}`,
      },
      launchMessage: "Project not found",
    };
  }

  const instance = getInstance(project.instanceId);
  if (!instance) {
    return {
      ok: false,
      probe: {
        reachable: false,
        status: "unknown",
        degraded: true,
        message: "Linked instance missing",
      },
      launchMessage: "Linked instance missing",
    };
  }

  updateInstanceStatus(instance.id, "starting");

  const engine = runEngine("ensure", instance);
  const launchMessage = String(
    engine.payload.message ??
      engine.stderr ??
      (engine.ok ? "Launch requested" : "Launch failed"),
  );

  const probe = await probeInstanceDb(instance);

  return {
    ok: engine.ok && probe.reachable,
    probe,
    launchMessage,
  };
}

export async function launchInstanceDb(instanceId: string): Promise<{
  ok: boolean;
  probe: DbProbeResult;
  launchMessage: string;
}> {
  // TODO: entitlement check — block instance launch without billing/auth gate.
  const instance = getInstance(instanceId);
  if (!instance) {
    return {
      ok: false,
      probe: {
        reachable: false,
        status: "unknown",
        degraded: true,
        message: `Instance not found: ${instanceId}`,
      },
      launchMessage: "Instance not found",
    };
  }

  updateInstanceStatus(instance.id, "starting");
  const engine = runEngine("ensure", instance);
  const launchMessage = String(
    engine.payload.message ??
      engine.stderr ??
      (engine.ok ? "Launch requested" : "Launch failed"),
  );
  const probe = await probeInstanceDb(instance);

  return {
    ok: engine.ok && probe.reachable,
    probe,
    launchMessage,
  };
}
