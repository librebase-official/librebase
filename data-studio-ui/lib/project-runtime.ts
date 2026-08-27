import { spawnSync } from "node:child_process";
import net from "node:net";
import path from "node:path";
import {
  getInstanceStatus,
  getK8sServiceUrl,
  provisionDedicatedInstance,
} from "./k8s-provisioner";
import { isSaasHarness } from "./runtime-env";
import {
  getLicontainerInstanceStatus,
  provisionLicontainerInstance,
} from "./licontainer-provisioner";
import { DEFAULT_DEV_RUNTIME_IMAGE, LIDB_RUNTIME_IMAGE } from "./k8s-manifests";
import { getInstance, getInstanceAsync, updateInstanceStatusAsync } from "./instances-store";
import { getProject, getProjectAsync } from "./projects-store";
import { getHostAsync } from "./hosts-store";
import { requireEntitlement } from "./entitlements";
import type { DbProbeResult, Host, Instance, Project, RuntimeMode } from "./types";

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

function engineEnv(instance: Instance): NodeJS.ProcessEnv {
  const env: NodeJS.ProcessEnv = {
    ...process.env,
    LI_DATA_DIR: instance.dataDir,
  };
  if (!process.env.LIDB_RUNTIME_MODE && !process.env.LIDB_ROOT) {
    env.LIDB_RUNTIME_MODE = "dev";
  }
  return env;
}

function parseRuntimeMode(value: unknown): RuntimeMode | undefined {
  if (value === "dev" || value === "production" || value === "unavailable") {
    return value;
  }
  return undefined;
}

function inferK8sRuntimeMode(): RuntimeMode {
  const image = LIDB_RUNTIME_IMAGE;
  if (image === DEFAULT_DEV_RUNTIME_IMAGE || image.endsWith(":dev")) {
    return "dev";
  }
  if (image.includes(":stub")) {
    return "unavailable";
  }
  return "production";
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
      env: engineEnv(instance),
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

/** Host advertised on connect strings. Never use the Studio container loopback in prod. */
export function defaultInstanceHost(): string {
  const fromEnv = process.env.LIBREBASE_INSTANCE_PUBLIC_HOST?.trim();
  if (fromEnv) return fromEnv;
  return "127.0.0.1";
}

export function getApiUrl(instance: Instance, hostIp?: string): string {
  if (instance.runtimeTarget === "kubernetes") {
    // SaaS harness is Hetzner-only — never surface an in-cluster DNS name
    // (http://svc.ns.svc.cluster.local:port) to the browser. OSS keeps k8s.
    if (isSaasHarness()) {
      const h = hostIp?.trim() || defaultInstanceHost();
      // If still loopback in SaaS without a VM, caller can decide to hide it.
      return `http://${h}:${instance.ports.api}`;
    }
    return getK8sServiceUrl(instance);
  }
  const h = hostIp?.trim() || defaultInstanceHost();
  return `http://${h}:${instance.ports.api}`;
}

export function getPostgresUrl(instance: Instance, hostIp?: string): string {
  if (instance.runtimeTarget === "kubernetes") {
    if (isSaasHarness()) {
      const h = hostIp?.trim() || defaultInstanceHost();
      return `postgresql://${h}:${instance.ports.postgres}/librebase`;
    }
    const host = getK8sServiceUrl(instance)
      .replace("http://", "")
      .replace(/:\d+$/, "");
    return `postgresql://${host}:${instance.ports.postgres}/librebase`;
  }
  const h = hostIp?.trim() || defaultInstanceHost();
  return `postgresql://${h}:${instance.ports.postgres}/librebase`;
}

export function getProjectUrls(
  project: Project,
  instance?: Instance,
  hostIp?: string,
): {
  apiUrl: string;
  postgresUrl: string;
} | null {
  const resolved = instance ?? getInstance(project.instanceId);
  if (!resolved) return null;
  return {
    apiUrl: getApiUrl(resolved, hostIp),
    postgresUrl: getPostgresUrl(resolved, hostIp),
  };
}

async function resolveInstanceHostIp(instance: Instance): Promise<string | undefined> {
  if (!instance.hostId) return undefined;
  const host = await getHostAsync(instance.hostId, instance.orgId);
  return host?.ip?.trim() || undefined;
}

export async function getProjectUrlsAsync(project: Project): Promise<{
  apiUrl: string;
  postgresUrl: string;
} | null> {
  const instance = await getInstanceAsync(project.instanceId, project.orgId);
  if (!instance) return null;
  const hostIp = await resolveInstanceHostIp(instance);
  return {
    apiUrl: getApiUrl(instance, hostIp),
    postgresUrl: getPostgresUrl(instance, hostIp),
  };
}

async function probeK8sInstance(instance: Instance): Promise<DbProbeResult> {
  const k8s = getInstanceStatus(instance.id);
  const reachable = k8s.status === "running" && !k8s.degraded;
  return {
    reachable,
    status: k8s.status,
    degraded: k8s.degraded,
    message: k8s.message,
    runtimeMode: inferK8sRuntimeMode(),
  };
}

async function probeLicontainerInstance(instance: Instance): Promise<DbProbeResult> {
  const lc = getLicontainerInstanceStatus(instance.id);
  const reachable = lc.status === "running" && !lc.degraded;
  return {
    reachable,
    status: lc.status,
    degraded: lc.degraded,
    message: lc.message,
    runtimeMode: inferK8sRuntimeMode(),
  };
}

export async function probeInstanceDb(instance: Instance): Promise<DbProbeResult> {
  if (instance.runtimeTarget === "kubernetes") {
    if (isSaasHarness()) {
      // SaaS harness does not run its own cluster — Hetzner is the upsell.
      // Don't surface "Kubernetes cluster unreachable — degraded mode (check KUBECONFIG)".
      return {
        reachable: false,
        status: "stopped",
        degraded: true,
        message:
          "Kubernetes is OSS-only. This SaaS project runs on Hetzner — provision a VM or use a local instance.",
        runtimeMode: "unavailable",
      };
    }
    return probeK8sInstance(instance);
  }

  if (instance.runtimeTarget === "licontainer") {
    return probeLicontainerInstance(instance);
  }

  const host = instance.hostId ? await resolveHost(instance) : undefined;

  // VM still booting — do not persist "starting" (that would make the host
  // agent try to run containers before the box is up). UI shows a spinner.
  if (host && (host.status === "provisioning" || host.status === "starting")) {
    return {
      reachable: false,
      status: "starting",
      degraded: false,
      message: "Waiting for VM " + host.name + " to finish booting",
      runtimeMode: "unavailable",
    };
  }

  // Instance lives on a rented VM: the host agent runs lidb-runtime there, so we
  // probe the VM's public IP (NOT localhost) and skip the local engine.
  if (host && host.ip && host.status === "running") {
    const apiUp = await isPortOpen(host.ip, instance.ports.api);
    const pgUp = await isPortOpen(host.ip, instance.ports.postgres);
    const portsUp = apiUp && pgUp;
    const status = portsUp ? "running" : instance.status === "starting" ? "starting" : "stopped";
    await updateInstanceStatusAsync(instance.id, status, instance.orgId);
    return {
      reachable: portsUp && status === "running",
      status,
      degraded: !portsUp,
      message: portsUp
        ? "Running on host " + (instance.hostId || "")
        : "Host " + (instance.hostId || "") + " not serving yet",
      runtimeMode: portsUp ? "production" : "unavailable",
    };
  }

  const engine = runEngine("status", instance);
  const engineStatus = String(engine.payload.status ?? "unknown");
  const degraded = Boolean(engine.payload.degraded);
  const runtimeMode = parseRuntimeMode(engine.payload.runtime_mode);
  const message = String(
    engine.payload.message ??
      engine.stderr ??
      (degraded ? "Runtime unavailable (degraded mode)" : "Status probe complete"),
  );

  const portOpen = await isPortOpen("127.0.0.1", instance.ports.api);
  const postgresOpen = await isPortOpen("127.0.0.1", instance.ports.postgres);
  const portsUp = portOpen && postgresOpen;

  let status = instance.status;
  if (engine.ok && engineStatus === "running" && portsUp) {
    status = "running";
  } else if (engineStatus === "starting") {
    status = "starting";
  } else if ((degraded && !portsUp) || !engine.ok) {
    status = "stopped";
  } else if (!portsUp) {
    status = "stopped";
  }

  await updateInstanceStatusAsync(instance.id, status, instance.orgId);

  return {
    reachable: portsUp && status === "running",
    status,
    degraded: degraded || !engine.ok,
    message,
    runtimeMode,
  };
}

// Best-effort probe for page rendering: a failing admin API or port check
// degrades the row's status instead of crashing the whole RSC page.
export async function probeInstanceDbSafe(instance: Instance): Promise<DbProbeResult> {
  try {
    return await probeInstanceDb(instance);
  } catch (err) {
    return {
      reachable: false,
      status: instance.status === "starting" ? "starting" : "stopped",
      degraded: true,
      message: "Status probe failed: " + (err instanceof Error ? err.message : String(err)),
      runtimeMode: "unavailable",
    };
  }
}

async function resolveHost(instance: Instance): Promise<Host | undefined> {
  return getHostAsync(instance.hostId!, instance.orgId);
}

async function launchProcessOrHost(instance: Instance): Promise<{
  ok: boolean;
  probe: DbProbeResult;
  launchMessage: string;
}> {
  // Rented VM: the host agent runs lidb-runtime there. Do not spawn a local
  // engine inside the Studio container (that is 127.0.0.1 and has no lis).
  if (instance.hostId) {
    const host = await resolveHost(instance);
    if (!host) {
      return {
        ok: false,
        probe: {
          reachable: false,
          status: "unknown",
          degraded: true,
          message: "Host not found for this instance",
        },
        launchMessage: "Host not found",
      };
    }
    if (host.status !== "running" || !host.ip) {
      return {
        ok: false,
        probe: {
          reachable: false,
          status: "stopped",
          degraded: true,
          message:
            "Host " + host.name + " is " + host.status + " — instance will start once it is running",
        },
        launchMessage: "Host not running yet; instance scheduled onto " + host.name,
      };
    }
    const probe = await probeInstanceDb(instance);
    return {
      ok: probe.reachable,
      probe,
      launchMessage:
        "Instance scheduled onto host " + host.name + " (" + host.ip + "); the host agent is starting it",
    };
  }

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

export async function probeProjectDb(projectId: string): Promise<DbProbeResult> {
  const project = await getProjectAsync(projectId);
  if (!project) {
    return {
      reachable: false,
      status: "unknown",
      degraded: true,
      message: `Project not found: ${projectId}`,
    };
  }

  const instance = await getInstanceAsync(project.instanceId, project.orgId);
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
  await requireEntitlement("instance.launch");
  const project = await getProjectAsync(projectId);
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

  const instance = await getInstanceAsync(project.instanceId, project.orgId);
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

  await updateInstanceStatusAsync(instance.id, "starting", instance.orgId);

  if (instance.runtimeTarget === "kubernetes") {
    if (isSaasHarness()) {
      return {
        ok: false,
        probe: await probeInstanceDb(instance),
        launchMessage:
          "Kubernetes is OSS-only. Provision a Hetzner VM for this SaaS project.",
      };
    }
    await requireEntitlement("k8s.provision", instance.orgId);
    const provision = provisionDedicatedInstance(instance);
    const probe = await probeInstanceDb(instance);
    return {
      ok: provision.ok && probe.reachable,
      probe,
      launchMessage: provision.message,
    };
  }

  if (instance.runtimeTarget === "licontainer") {
    const provision = provisionLicontainerInstance(instance);
    const probe = await probeInstanceDb(instance);
    return {
      ok: provision.ok && probe.reachable,
      probe,
      launchMessage: provision.message,
    };
  }

  return launchProcessOrHost(instance);
}

async function stopInstanceRuntime(instance: Instance): Promise<{
  ok: boolean;
  probe: DbProbeResult;
  message: string;
}> {
  if (instance.runtimeTarget === "kubernetes" || instance.runtimeTarget === "licontainer") {
    await updateInstanceStatusAsync(instance.id, "stopped", instance.orgId);
    return {
      ok: true,
      probe: {
        reachable: false,
        status: "stopped",
        degraded: false,
        message: "Marked stopped — the orchestrator must drain the pod.",
      },
      message: "Marked stopped. Orchestrated runtimes are not killed from Studio yet.",
    };
  }

  if (instance.hostId) {
    await updateInstanceStatusAsync(instance.id, "stopped", instance.orgId);
    return {
      ok: true,
      probe: {
        reachable: false,
        status: "stopped",
        degraded: false,
        message: "Pause requested on the host agent.",
      },
      message: "Pause recorded. The host agent stops the process on its next sync.",
    };
  }

  const engine = runEngine("stop", instance);
  await updateInstanceStatusAsync(instance.id, "stopped", instance.orgId);
  const probe = await probeInstanceDb(instance);
  return {
    ok: !probe.reachable,
    probe,
    message: String(engine.payload.message ?? engine.stderr ?? "Stop requested"),
  };
}

export async function pauseProjectDb(projectId: string): Promise<{
  ok: boolean;
  probe: DbProbeResult;
  message: string;
}> {
  const project = await getProjectAsync(projectId);
  if (!project) {
    return {
      ok: false,
      probe: {
        reachable: false,
        status: "unknown",
        degraded: true,
        message: `Project not found: ${projectId}`,
      },
      message: "Project not found",
    };
  }
  const instance = await getInstanceAsync(project.instanceId, project.orgId);
  if (!instance) {
    return {
      ok: false,
      probe: {
        reachable: false,
        status: "unknown",
        degraded: true,
        message: "Linked instance missing",
      },
      message: "Linked instance missing",
    };
  }

  return stopInstanceRuntime(instance);
}

export async function pauseInstanceDb(instanceId: string): Promise<{
  ok: boolean;
  probe: DbProbeResult;
  message: string;
}> {
  const instance = await getInstanceAsync(instanceId);
  if (!instance) {
    return {
      ok: false,
      probe: {
        reachable: false,
        status: "unknown",
        degraded: true,
        message: `Instance not found: ${instanceId}`,
      },
      message: "Instance not found",
    };
  }
  return stopInstanceRuntime(instance);
}

export async function launchInstanceDb(instanceId: string): Promise<{
  ok: boolean;
  probe: DbProbeResult;
  launchMessage: string;
}> {
  await requireEntitlement("instance.launch");
  const instance = await getInstanceAsync(instanceId);
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

  await updateInstanceStatusAsync(instance.id, "starting", instance.orgId);

  if (instance.runtimeTarget === "kubernetes") {
    if (isSaasHarness()) {
      return {
        ok: false,
        probe: await probeInstanceDb(instance),
        launchMessage:
          "Kubernetes is OSS-only. Provision a Hetzner VM for this SaaS project.",
      };
    }
    await requireEntitlement("k8s.provision", instance.orgId);
    const provision = provisionDedicatedInstance(instance);
    const probe = await probeInstanceDb(instance);
    return {
      ok: provision.ok && probe.reachable,
      probe,
      launchMessage: provision.message,
    };
  }

  if (instance.runtimeTarget === "licontainer") {
    const provision = provisionLicontainerInstance(instance);
    const probe = await probeInstanceDb(instance);
    return {
      ok: provision.ok && probe.reachable,
      probe,
      launchMessage: provision.message,
    };
  }

  return launchProcessOrHost(instance);
}
