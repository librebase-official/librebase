export type RuntimeTarget = "local" | "kubernetes" | "licontainer";

/** Container backend used when runtime is kubernetes. */
export type K8sContainerRuntime = "containerd" | "licontainer";

/**
 * Localhost engine (spawn lidb on 127.0.0.1 of the Studio host) is a
 * developer escape hatch, not a SaaS product path. Opt in with
 * LIBREBASE_ALLOW_LOCAL=1. Tests set that in vitest.config.ts.
 */
export function isLocalRuntimeAllowed(): boolean {
  const raw = process.env.LIBREBASE_ALLOW_LOCAL?.trim().toLowerCase();
  return raw === "1" || raw === "true" || raw === "yes";
}

/** Default runtime target from env; SaaS does not fall back to localhost. */
export function getLibrebaseRuntime(): RuntimeTarget {
  const raw = process.env.LIBREBASE_RUNTIME?.trim().toLowerCase();
  if (raw === "kubernetes") return "kubernetes";
  if (raw === "licontainer") return "licontainer";
  if (raw === "local" && isLocalRuntimeAllowed()) return "local";
  if (isLocalRuntimeAllowed()) return "local";
  return "kubernetes";
}

export function resolveRuntimeTarget(override?: RuntimeTarget): RuntimeTarget {
  if (override === "local" && !isLocalRuntimeAllowed()) {
    return getLibrebaseRuntime();
  }
  return override ?? getLibrebaseRuntime();
}

export function assertLocalRuntimeAllowed(action = "local runtime"): void {
  if (!isLocalRuntimeAllowed()) {
    throw new Error(
      `${action} is disabled on this Librebase SaaS. Provision a host VM (or Kubernetes). Set LIBREBASE_ALLOW_LOCAL=1 only for local development.`,
    );
  }
}

export function getKubeconfigPath(): string | undefined {
  const raw = process.env.KUBECONFIG?.trim();
  return raw || undefined;
}

/** K8s node container runtime (containerd default; licontainer when RuntimeClass set). */
export function getK8sContainerRuntime(): K8sContainerRuntime {
  const raw = process.env.LIBREBASE_K8S_CONTAINER_RUNTIME?.trim().toLowerCase();
  return raw === "licontainer" ? "licontainer" : "containerd";
}

/** Human-readable backend label for Instances UI. */
export function runtimeBackendLabel(
  runtimeTarget: RuntimeTarget,
  k8sRuntime?: K8sContainerRuntime,
): string {
  if (runtimeTarget === "licontainer") return "lictl";
  if (runtimeTarget === "kubernetes") {
    return k8sRuntime === "licontainer" ? "k8s+licontainer" : "k8s+containerd";
  }
  return "local";
}
