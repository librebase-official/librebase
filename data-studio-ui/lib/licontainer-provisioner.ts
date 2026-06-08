import { spawnSync } from "node:child_process";
import { getInstance, updateInstance } from "./instances-store";
import { LIDB_RUNTIME_IMAGE } from "./k8s-manifests";
import type { Instance, InstanceStatus } from "./types";

export interface LicontainerProvisionResult {
  ok: boolean;
  degraded: boolean;
  message: string;
  containerId?: string;
}

export interface LicontainerInstanceStatus {
  instanceId: string;
  status: InstanceStatus;
  degraded: boolean;
  message: string;
  containerId?: string;
  state?: string;
}

function lictlBinary(): string {
  return process.env.LICTL ?? "lictl";
}

function daemonReachable(): boolean {
  const socket =
    process.env.LI_CONTAINER_SOCKET ?? "/run/licontainer/licontainerd.sock";
  const result = spawnSync(
    process.platform === "win32" ? "wsl" : "test",
    process.platform === "win32"
      ? ["-d", process.env.LI_CONTAINER_WSL_DISTRO ?? "LibrebaseContainer", "-e", "test", "-S", socket]
      : ["-S", socket],
    { encoding: "utf8", timeout: 5_000 },
  );
  return result.status === 0;
}

function runLictl(args: string[]): {
  ok: boolean;
  stdout: string;
  stderr: string;
} {
  const result = spawnSync(lictlBinary(), args, {
    encoding: "utf8",
    timeout: 120_000,
  });
  return {
    ok: result.status === 0,
    stdout: (result.stdout ?? "").trim(),
    stderr: (result.stderr ?? "").trim(),
  };
}

/** Check whether licontainerd is reachable (honest — no fake green). */
export function isLicontainerAvailable(): boolean {
  return daemonReachable();
}

/** Pull and run lidb-runtime image for an instance via lictl. */
export function provisionLicontainerInstance(
  instance: Instance,
): LicontainerProvisionResult {
  // TODO: entitlement check — block pull/create without billing gate.
  if (!isLicontainerAvailable()) {
    updateInstance(instance.id, {
      status: "error",
      k8sDegraded: true,
      k8sMessage:
        "licontainerd unreachable — degraded mode (start daemon or WSL bridge)",
    });
    return {
      ok: false,
      degraded: true,
      message:
        "licontainerd unreachable — degraded mode (check LI_CONTAINER_SOCKET or WSL)",
    };
  }

  const image = process.env.LIBREBASE_LICONTAINER_IMAGE ?? LIDB_RUNTIME_IMAGE;
  const name = `librebase-${instance.id}`;

  const pull = runLictl(["pull", image]);
  if (!pull.ok) {
    updateInstance(instance.id, {
      status: "error",
      k8sDegraded: true,
      k8sMessage: pull.stderr || "lictl pull failed",
    });
    return {
      ok: false,
      degraded: true,
      message: pull.stderr || "lictl pull failed",
    };
  }

  const run = runLictl(["run", "--name", name, image]);
  if (!run.ok) {
    updateInstance(instance.id, {
      status: "error",
      k8sDegraded: true,
      k8sMessage: run.stderr || "lictl run failed",
    });
    return {
      ok: false,
      degraded: true,
      message: run.stderr || "lictl run failed",
    };
  }

  updateInstance(instance.id, {
    status: "running",
    k8sDegraded: false,
    k8sMessage: `licontainer container ${name} started`,
  });

  return {
    ok: true,
    degraded: false,
    message: `Started licontainer container ${name}`,
    containerId: name,
  };
}

/** Query container status via lictl ps (best-effort parse). */
export function getLicontainerInstanceStatus(
  instanceId: string,
): LicontainerInstanceStatus {
  const instance = getInstance(instanceId);
  if (!instance) {
    return {
      instanceId,
      status: "unknown",
      degraded: true,
      message: `Instance not found: ${instanceId}`,
    };
  }

  if (!isLicontainerAvailable()) {
    return {
      instanceId,
      status: "error",
      degraded: true,
      message: "licontainerd unreachable — degraded mode",
    };
  }

  const ps = runLictl(["ps"]);
  if (!ps.ok) {
    return {
      instanceId,
      status: "error",
      degraded: true,
      message: ps.stderr || "lictl ps failed",
    };
  }

  const name = `librebase-${instanceId}`;
  const running = ps.stdout.includes(name) && ps.stdout.includes("running");

  return {
    instanceId,
    status: running ? "running" : "stopped",
    degraded: !running,
    message: running
      ? `Container ${name} running`
      : `Container ${name} not running`,
    containerId: name,
    state: running ? "running" : "stopped",
  };
}

/** Stop licontainer instance. */
export function stopLicontainerInstance(instanceId: string): LicontainerProvisionResult {
  const name = `librebase-${instanceId}`;
  const stop = runLictl(["stop", name]);
  if (!stop.ok) {
    return {
      ok: false,
      degraded: true,
      message: stop.stderr || "lictl stop failed",
    };
  }
  updateInstance(instanceId, { status: "stopped" });
  return { ok: true, degraded: false, message: `Stopped ${name}` };
}
