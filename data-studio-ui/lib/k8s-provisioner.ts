import { spawnSync } from "node:child_process";
import { getInstance, updateInstance } from "./instances-store";
import {
  buildDedicatedManifests,
  buildSharedInstanceManifests,
  buildSharedProjectConfigMap,
  dedicatedNamespace,
  sharedNamespace,
} from "./k8s-manifests";
import { getKubeconfigPath, getK8sContainerRuntime, isSaasHarness } from "./runtime-env";
import type { Instance, InstanceStatus, Project } from "./types";

export interface K8sProvisionResult {
  ok: boolean;
  degraded: boolean;
  message: string;
  namespace?: string;
}

export interface K8sInstanceStatus {
  instanceId: string;
  namespace: string;
  status: InstanceStatus;
  degraded: boolean;
  message: string;
  podPhase?: string;
  ready?: boolean;
}

function kubectlBinary(): string {
  return process.env.KUBECTL ?? "kubectl";
}

export function isClusterAvailable(): boolean {
  const result = spawnSync(
    kubectlBinary(),
    ["cluster-info", "--request-timeout=5s"],
    {
      encoding: "utf8",
      env: kubectlEnv(),
      timeout: 10_000,
    },
  );
  return result.status === 0;
}

function kubectlEnv(): NodeJS.ProcessEnv {
  const kubeconfig = getKubeconfigPath();
  if (!kubeconfig) return { ...process.env };
  return { ...process.env, KUBECONFIG: kubeconfig };
}

function runKubectl(args: string[]): {
  ok: boolean;
  stdout: string;
  stderr: string;
} {
  const result = spawnSync(kubectlBinary(), args, {
    encoding: "utf8",
    env: kubectlEnv(),
    timeout: 60_000,
  });
  return {
    ok: result.status === 0,
    stdout: (result.stdout ?? "").trim(),
    stderr: (result.stderr ?? "").trim(),
  };
}

function applyManifests(yaml: string): K8sProvisionResult {
  if (!isClusterAvailable()) {
    if (isSaasHarness()) {
      return {
        ok: false,
        degraded: true,
        message:
          "Kubernetes is OSS-only — this SaaS harness provisions Hetzner VMs instead. Set LIBREBASE_HARNESS=oss to use your own cluster.",
      };
    }
    return {
      ok: false,
      degraded: true,
      message: "Kubernetes cluster unreachable — degraded mode (check KUBECONFIG)",
    };
  }

  const child = spawnSync(kubectlBinary(), ["apply", "-f", "-"], {
    encoding: "utf8",
    input: yaml,
    env: kubectlEnv(),
    timeout: 120_000,
  });

  if (child.status !== 0) {
    const err = (child.stderr ?? child.stdout ?? "kubectl apply failed").trim();
    return { ok: false, degraded: false, message: err };
  }

  return {
    ok: true,
    degraded: false,
    message: (child.stdout ?? "").trim() || "Manifests applied",
  };
}

function instanceNamespace(instance: Instance): string {
  return instance.deploymentMode === "shared"
    ? sharedNamespace(instance.orgId)
    : dedicatedNamespace(instance.id);
}

/** Provision a dedicated (or shared-base) instance on Kubernetes. */
export function provisionDedicatedInstance(instance: Instance): K8sProvisionResult {
  if (isSaasHarness()) {
    return {
      ok: false,
      degraded: true,
      message:
        "Kubernetes is OSS-only — this SaaS harness provisions Hetzner VMs instead. Set LIBREBASE_HARNESS=oss to use your own cluster.",
    };
  }
  // Entitlement gates are enforced at API launch/create entry points.
  const ns = instanceNamespace(instance);
  const yaml =
    instance.deploymentMode === "shared"
      ? buildSharedInstanceManifests({ instance })
      : buildDedicatedManifests({
          instance,
          containerRuntime: getK8sContainerRuntime(),
        });

  const result = applyManifests(yaml);
  if (result.ok) {
    updateInstance(instance.id, {
      k8sNamespace: ns,
      k8sDegraded: false,
      k8sMessage: result.message,
    });
    result.namespace = ns;
  } else if (result.degraded) {
    updateInstance(instance.id, {
      k8sNamespace: ns,
      k8sDegraded: true,
      k8sMessage: result.message,
    });
    result.namespace = ns;
  }
  return result;
}

/** Attach a shared project via ConfigMap in the org shared namespace. */
export function attachSharedProject(
  instance: Instance,
  project: Project,
): K8sProvisionResult {
  if (isSaasHarness()) {
    return {
      ok: false,
      degraded: true,
      message:
        "Kubernetes is OSS-only — this SaaS harness provisions Hetzner VMs instead.",
    };
  }
  // Entitlement gates are enforced at API launch/create entry points.
  if (instance.deploymentMode !== "shared") {
    return {
      ok: false,
      degraded: false,
      message: "attachSharedProject requires a shared deployment instance",
    };
  }

  const yaml = buildSharedProjectConfigMap({ instance, project });
  const result = applyManifests(yaml);
  if (result.ok || result.degraded) {
    result.namespace = sharedNamespace(instance.orgId);
  }
  return result;
}

function mapPodPhase(phase: string | undefined, ready: boolean): InstanceStatus {
  if (!phase) return "unknown";
  if (phase === "Running" && ready) return "running";
  if (phase === "Pending") return "starting";
  if (phase === "Running" && !ready) return "starting";
  if (phase === "Failed" || phase === "Unknown") return "error";
  return "stopped";
}

/** Query Kubernetes for instance pod health (honest — no fake green). */
export function getInstanceStatus(instanceId: string): K8sInstanceStatus {
  if (isSaasHarness()) {
    const inst = getInstance(instanceId);
    const ns = inst ? (inst.k8sNamespace ?? instanceNamespace(inst)) : "";
    return {
      instanceId,
      namespace: ns,
      status: "stopped",
      degraded: true,
      message:
        "Kubernetes is OSS-only — this SaaS harness uses Hetzner. Provision a VM instead.",
    };
  }
  const instance = getInstance(instanceId);
  if (!instance) {
    return {
      instanceId,
      namespace: "",
      status: "unknown",
      degraded: true,
      message: `Instance not found: ${instanceId}`,
    };
  }

  const ns = instance.k8sNamespace ?? instanceNamespace(instance);

  if (!isClusterAvailable()) {
    if (isSaasHarness()) {
      return {
        instanceId,
        namespace: ns,
        status: "stopped",
        degraded: true,
        message:
          "Kubernetes is OSS-only — this SaaS harness uses Hetzner. Provision a VM instead.",
      };
    }
    return {
      instanceId,
      namespace: ns,
      status: "stopped",
      degraded: true,
      message: "Kubernetes cluster unreachable — degraded mode",
    };
  }

  const getNs = runKubectl(["get", "namespace", ns, "-o", "jsonpath={.metadata.name}"]);
  if (!getNs.ok || !getNs.stdout) {
    return {
      instanceId,
      namespace: ns,
      status: "stopped",
      degraded: false,
      message: "Not provisioned on cluster (namespace missing)",
    };
  }

  const deployName =
    instance.deploymentMode === "shared"
      ? `librebase-runtime-${instance.id}`
      : "librebase-runtime";

  const podJson = runKubectl([
    "get",
    "pods",
    "-n",
    ns,
    "-l",
    `librebase.io/instance=${instance.id}`,
    "-o",
    "jsonpath={.items[0].status.phase},{.items[0].status.conditions[?(@.type=='Ready')].status}",
  ]);

  let podPhase: string | undefined;
  let ready = false;
  if (podJson.ok && podJson.stdout) {
    const [phase, readyStatus] = podJson.stdout.split(",");
    podPhase = phase || undefined;
    ready = readyStatus === "True";
  }

  const status = mapPodPhase(podPhase, ready);
  const message =
    podPhase === undefined
      ? "No pods found for instance"
      : `Pod phase: ${podPhase}${ready ? " (ready)" : ""}`;

  updateInstance(instance.id, {
    status,
    k8sNamespace: ns,
    k8sDegraded: false,
    k8sMessage: message,
  });

  return {
    instanceId,
    namespace: ns,
    status,
    degraded: false,
    message,
    podPhase,
    ready,
  };
}

/** Remove instance resources from the cluster. */
export function deleteK8sInstance(instanceId: string): K8sProvisionResult {
  if (isSaasHarness()) {
    return {
      ok: false,
      degraded: true,
      message: "Kubernetes is OSS-only — nothing to delete in SaaS harness.",
    };
  }
  const instance = getInstance(instanceId);
  if (!instance) {
    return { ok: false, degraded: true, message: `Instance not found: ${instanceId}` };
  }

  if (!isClusterAvailable()) {
    if (isSaasHarness()) {
      return {
        ok: false,
        degraded: true,
        message: "Kubernetes is OSS-only — nothing to delete in SaaS harness.",
      };
    }
    return {
      ok: false,
      degraded: true,
      message: "Kubernetes cluster unreachable — cannot delete",
    };
  }

  const ns = instance.k8sNamespace ?? instanceNamespace(instance);

  if (instance.deploymentMode === "dedicated") {
    const result = runKubectl(["delete", "namespace", ns, "--wait=false"]);
    if (!result.ok) {
      return { ok: false, degraded: false, message: result.stderr || "Delete failed" };
    }
    return { ok: true, degraded: false, message: `Deleted namespace ${ns}`, namespace: ns };
  }

  const deployName = `librebase-runtime-${instance.id}`;
  const delDeploy = runKubectl(["delete", "deployment", deployName, "-n", ns, "--ignore-not-found"]);
  const delSvc = runKubectl([
    "delete",
    "service",
    `librebase-api-${instance.id}`,
    "-n",
    ns,
    "--ignore-not-found",
  ]);
  const delPvc = runKubectl([
    "delete",
    "pvc",
    `librebase-data-${instance.id}`,
    "-n",
    ns,
    "--ignore-not-found",
  ]);
  const delCm = runKubectl([
    "delete",
    "configmap",
    `librebase-config-${instance.id}`,
    "-n",
    ns,
    "--ignore-not-found",
  ]);

  const ok = delDeploy.ok && delSvc.ok && delPvc.ok && delCm.ok;
  return {
    ok,
    degraded: false,
    message: ok ? `Removed shared instance ${instanceId} from ${ns}` : "Partial delete",
    namespace: ns,
  };
}

export function getK8sServiceUrl(instance: Instance): string {
  const ns = instance.k8sNamespace ?? instanceNamespace(instance);
  const svc =
    instance.deploymentMode === "shared"
      ? `librebase-api-${instance.id}`
      : "librebase-api";
  return `http://${svc}.${ns}.svc.cluster.local:${instance.ports.api}`;
}
