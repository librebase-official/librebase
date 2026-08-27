export type RuntimeTarget = "local" | "kubernetes" | "licontainer";

/** Harness flavour: OSS runs local/k8s, SaaS is Hetzner-only (upsell). */
export type HarnessMode = "oss" | "saas";

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

export function getHarnessMode(): HarnessMode {
  const raw = (
    process.env.LIBREBASE_HARNESS ??
    process.env.NEXT_PUBLIC_HARNESS ??
    ""
  )
    .trim()
    .toLowerCase();
  if (raw === "saas" || raw === "hetzner") return "saas";
  if (raw === "oss" || raw === "local" || raw === "k8s") return "oss";
  // This repo is librebase-saas — defaults to SaaS (Hetzner-only) for now.
  // Set LIBREBASE_HARNESS=oss to re-enable local/k8s (OSS harness where
  // KUBECONFIG and svc.cluster.local are expected).
  // The old heuristic (HETZNER token / ADMIN_URL) is kept as an explicit
  // SaaS signal but no longer required for the default.
  return "saas";
}

export function isSaasHarness(): boolean {
  return getHarnessMode() === "saas";
}

export function isOssHarness(): boolean {
  return !isSaasHarness();
}
