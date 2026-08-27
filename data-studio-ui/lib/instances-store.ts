import fs from "node:fs";
import { resolveRuntimeTarget } from "./runtime-env";
import { deleteK8sInstance } from "./k8s-provisioner";
import {
  adminCreateInstance,
  adminApiEnabled,
  adminDeleteInstance,
  adminGetInstance,
  adminListInstances,
  adminPatchInstance,
} from "./librebase-admin-client";
import { resolveStudioOrgId, studioOrgId } from "./org-context";
import type {
  CreateInstanceInput,
  DeploymentMode,
  Instance,
  InstancePorts,
  InstanceStatus,
  RuntimeTarget,
} from "./types";
import {
  generateId,
  instanceDataDir,
  readJsonFile,
  slugify,
  writeJsonFile,
} from "./json-store";
import { ensureStudioDataRoot } from "./studio-data-dir";

const INSTANCES_FILE = "instances.json";

const BASE_API_PORT = 54320;
const BASE_POSTGRES_PORT = 54322;
const PORT_BLOCK = 10;

function normalizeInstance(raw: Instance): Instance {
  return {
    ...raw,
    runtimeTarget: raw.runtimeTarget ?? "local",
  };
}

function loadInstances(): Instance[] {
  return readJsonFile<Instance[]>(INSTANCES_FILE, []).map(normalizeInstance);
}

function saveInstances(instances: Instance[]): void {
  writeJsonFile(INSTANCES_FILE, instances);
}

function allocatePorts(existing: Instance[]): InstancePorts {
  const usedApi = new Set(existing.map((i) => i.ports.api));
  const usedPg = new Set(existing.map((i) => i.ports.postgres));
  let block = 0;
  while (true) {
    const api = BASE_API_PORT + block * PORT_BLOCK;
    const postgres = BASE_POSTGRES_PORT + block * PORT_BLOCK;
    if (!usedApi.has(api) && !usedPg.has(postgres)) {
      return { api, postgres };
    }
    block += 1;
  }
}

export function listInstances(orgId = "default"): Instance[] {
  return loadInstances().filter((i) => i.orgId === orgId);
}

export function getInstance(id: string): Instance | undefined {
  return loadInstances().find((i) => i.id === id);
}

export function createInstance(input: CreateInstanceInput): Instance {
  const instances = loadInstances();
  const orgId = input.orgId ?? "default";
  const deploymentMode: DeploymentMode = input.deploymentMode ?? "dedicated";
  const id = generateId("inst");
  const dataDir = instanceDataDir(id);
  fs.mkdirSync(dataDir, { recursive: true });

  const now = new Date().toISOString();
  const runtimeTarget: RuntimeTarget = resolveRuntimeTarget(input.runtime);
  const instance: Instance = {
    id,
    name: input.name,
    orgId,
    dataDir,
    ports: allocatePorts(instances),
    status: "stopped",
    deploymentMode,
    runtimeTarget,
    createdAt: now,
    updatedAt: now,
  };

  instances.push(instance);
  saveInstances(instances);
  return instance;
}

export function updateInstanceStatus(
  id: string,
  status: InstanceStatus,
): Instance | undefined {
  const instances = loadInstances();
  const index = instances.findIndex((i) => i.id === id);
  if (index === -1) return undefined;

  instances[index] = {
    ...instances[index],
    status,
    updatedAt: new Date().toISOString(),
  };
  saveInstances(instances);
  return instances[index];
}

export function updateInstance(
  id: string,
  patch: Partial<
    Pick<
      Instance,
      "name" | "status" | "k8sNamespace" | "k8sDegraded" | "k8sMessage" | "runtimeTarget"
    >
  >,
): Instance | undefined {
  const instances = loadInstances();
  const index = instances.findIndex((i) => i.id === id);
  if (index === -1) return undefined;

  instances[index] = {
    ...instances[index],
    ...patch,
    updatedAt: new Date().toISOString(),
  };
  saveInstances(instances);
  return instances[index];
}

export function deleteInstance(id: string): boolean {
  const instances = loadInstances();
  const next = instances.filter((i) => i.id !== id);
  if (next.length === instances.length) return false;
  saveInstances(next);
  return true;
}

/** Default instance name derived from project name (dedicated provisioning). */
export function defaultInstanceName(projectName: string): string {
  const slug = slugify(projectName);
  return slug ? `${slug}-runtime` : "project-runtime";
}

export function ensureStudioRootForInstances(): string {
  return ensureStudioDataRoot();
}

/** Test helper — replace entire instance list. */
export function _setInstancesForTest(instances: Instance[]): void {
  saveInstances(instances);
}

/** Test helper — clear instances file. */
export function _clearInstancesForTest(): void {
  saveInstances([]);
}

export async function listInstancesAsync(orgId?: string): Promise<Instance[]> {
  const resolvedOrg = orgId ?? (await resolveStudioOrgId());
  if (!adminApiEnabled()) {
    return listInstances(resolvedOrg);
  }
  return adminListInstances(resolvedOrg);
}

export async function getInstanceAsync(
  id: string,
  orgId?: string,
): Promise<Instance | undefined> {
  if (!adminApiEnabled()) {
    return getInstance(id);
  }
  const resolvedOrg = orgId ?? (await resolveStudioOrgId());
  return adminGetInstance(resolvedOrg, id);
}

export async function createInstanceAsync(
  input: CreateInstanceInput,
): Promise<Instance> {
  const orgId = input.orgId ?? studioOrgId();
  if (!adminApiEnabled()) {
    return createInstance(input);
  }

  const existing = await adminListInstances(orgId);
  const ports = allocatePorts(existing);
  const runtimeTarget: RuntimeTarget = resolveRuntimeTarget(input.runtime);
  const deploymentMode: DeploymentMode = input.deploymentMode ?? "dedicated";
  const created = await adminCreateInstance(orgId, {
    ...input,
    orgId,
    ports,
    status: "stopped",
    runtimeTarget,
    deploymentMode,
    dataDir: "",
    hostId: input.hostId,
    memLimitMb: input.memLimitMb,
  });
  const dataDir = instanceDataDir(created.id);
  fs.mkdirSync(dataDir, { recursive: true });
  return adminPatchInstance(orgId, created.id, { dataDir });
}

export async function updateInstanceStatusAsync(
  id: string,
  status: InstanceStatus,
  orgId?: string,
): Promise<Instance | undefined> {
  if (!adminApiEnabled()) {
    return updateInstanceStatus(id, status);
  }
  const resolvedOrg = orgId ?? (await resolveStudioOrgId());
  return adminPatchInstance(resolvedOrg, id, { status });
}

export async function patchInstanceAsync(
  id: string,
  patch: Partial<
    Pick<
      Instance,
      | "name"
      | "status"
      | "dataDir"
      | "ports"
      | "k8sNamespace"
      | "k8sDegraded"
      | "k8sMessage"
      | "runtimeTarget"
    >
  >,
  orgId?: string,
): Promise<Instance | undefined> {
  if (!adminApiEnabled()) {
    return updateInstance(id, patch);
  }
  const resolvedOrg = orgId ?? (await resolveStudioOrgId());
  return adminPatchInstance(resolvedOrg, id, patch);
}

export async function deleteInstanceAsync(
  id: string,
  orgId?: string,
): Promise<boolean> {
  if (!adminApiEnabled()) {
    const instance = getInstance(id);
    if (!instance) return false;
    if (instance.runtimeTarget === "kubernetes") {
      deleteK8sInstance(id);
    }
    if (instance.dataDir) {
      fs.rmSync(instance.dataDir, { recursive: true, force: true });
    }
    return deleteInstance(id);
  }
  const resolvedOrg = orgId ?? (await resolveStudioOrgId());
  await adminDeleteInstance(resolvedOrg, id);
  return true;
}
