import type { RuntimeTarget } from "./runtime-env";

export type DeploymentMode = "dedicated" | "shared";

export type { RuntimeTarget };

export type InstanceStatus =
  | "stopped"
  | "starting"
  | "running"
  | "error"
  | "unknown";

export type HostStatus = "stopped" | "starting" | "running" | "error";

export interface InstancePorts {
  api: number;
  postgres: number;
}

export interface Host {
  id: string;
  orgId: string;
  name: string;
  provider: string;
  region: string;
  /** Total memory budget (MB) the rented VM provides. */
  memMb: number;
  /** Committed memory (MB) across placed instances. */
  memUsedMb: number;
  status: HostStatus;
  createdAt: string;
  updatedAt: string;
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
  /** Host VM this instance is placed on (multi-instance-per-VM). */
  hostId?: string;
  /** Memory limit (MB) reserved on the host for this instance. */
  memLimitMb?: number;
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
  /** Host VM to place this instance on. */
  hostId?: string;
  /** Memory limit (MB) reserved on the host. */
  memLimitMb?: number;
}

export interface CreateHostInput {
  name: string;
  orgId?: string;
  provider?: string;
  region?: string;
  /** Total memory budget (MB), e.g. 512. */
  memMb?: number;
}

export type RuntimeMode = "dev" | "production" | "unavailable";

export interface DbProbeResult {
  reachable: boolean;
  status: InstanceStatus;
  degraded: boolean;
  message: string;
  runtimeMode?: RuntimeMode;
}
