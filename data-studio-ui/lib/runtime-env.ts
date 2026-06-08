export type RuntimeTarget = "local" | "kubernetes";

/** Default runtime target from env; local for dev when unset. */
export function getLibrebaseRuntime(): RuntimeTarget {
  const raw = process.env.LIBREBASE_RUNTIME?.trim().toLowerCase();
  return raw === "kubernetes" ? "kubernetes" : "local";
}

export function resolveRuntimeTarget(override?: RuntimeTarget): RuntimeTarget {
  return override ?? getLibrebaseRuntime();
}

export function getKubeconfigPath(): string | undefined {
  const raw = process.env.KUBECONFIG?.trim();
  return raw || undefined;
}
