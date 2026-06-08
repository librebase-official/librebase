import fs from "node:fs";
import type {
  CreateInstanceInput,
  DeploymentMode,
  Instance,
  InstancePorts,
  InstanceStatus,
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

function loadInstances(): Instance[] {
  return readJsonFile<Instance[]>(INSTANCES_FILE, []);
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
  const instance: Instance = {
    id,
    name: input.name,
    orgId,
    dataDir,
    ports: allocatePorts(instances),
    status: "stopped",
    deploymentMode,
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
  patch: Partial<Pick<Instance, "name" | "status">>,
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
