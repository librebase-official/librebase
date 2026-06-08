import type { RuntimeTarget } from "./runtime-env";

export type DeploymentMode = "dedicated" | "shared";

export type { RuntimeTarget };

export type InstanceStatus =
  | "stopped"
  | "starting"
  | "running"
  | "error"
  | "unknown";

export interface InstancePorts {
  api: number;
  postgres: number;
}

export interface Instance {
  id: string;
  name: string;
  orgId: string;
  dataDir: string;
  ports: InstancePorts;
  status: InstanceStatus;
  deploymentMode: DeploymentMode;
  /** Where this instance runs: local lis process or Kubernetes. */
  runtimeTarget: RuntimeTarget;
  /** Populated when runtimeTarget is kubernetes. */
  k8sNamespace?: string;
  k8sDegraded?: boolean;
  k8sMessage?: string;
  createdAt: string;
  updatedAt: string;
}

export interface Project {
  id: string;
  name: string;
  orgId: string;
  instanceId: string;
  deploymentMode: DeploymentMode;
  region: string;
  createdAt: string;
  updatedAt: string;
}

export type RuntimeChoice = "new" | "existing";

export interface CreateProjectInput {
  name: string;
  orgId?: string;
  region?: string;
  runtimeChoice: RuntimeChoice;
  instanceId?: string;
  /** Override LIBREBASE_RUNTIME for this project/instance. */
  runtime?: RuntimeTarget;
}

export interface CreateInstanceInput {
  name: string;
  orgId?: string;
  deploymentMode?: DeploymentMode;
  runtime?: RuntimeTarget;
}

export interface DbProbeResult {
  reachable: boolean;
  status: InstanceStatus;
  degraded: boolean;
  message: string;
}
