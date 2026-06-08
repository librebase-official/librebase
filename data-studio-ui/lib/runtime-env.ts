export type RuntimeTarget = "local" | "kubernetes" | "licontainer";

/** Container backend used when runtime is kubernetes. */
export type K8sContainerRuntime = "containerd" | "licontainer";

/** Default runtime target from env; local for dev when unset. */
export function getLibrebaseRuntime(): RuntimeTarget {
  const raw = process.env.LIBREBASE_RUNTIME?.trim().toLowerCase();
  if (raw === "kubernetes") return "kubernetes";
  if (raw === "licontainer") return "licontainer";
  return "local";
}

export function resolveRuntimeTarget(override?: RuntimeTarget): RuntimeTarget {
  return override ?? getLibrebaseRuntime();
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
