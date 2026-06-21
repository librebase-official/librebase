import type { CreateProjectInput, DeploymentMode, Project } from "./types";
import {
  attachSharedProject,
  provisionDedicatedInstance,
} from "./k8s-provisioner";
import {
  createInstance,
  createInstanceAsync,
  defaultInstanceName,
  getInstance,
  getInstanceAsync,
} from "./instances-store";
import {
  liorgCreateProject,
  liorgEnabled,
  liorgGetProject,
  liorgListProjects,
} from "./liorg-client";
import { requireEntitlement } from "./entitlements";
import { resolveStudioOrgId, studioOrgId } from "./org-context";
import { generateId, readJsonFile, writeJsonFile } from "./json-store";

const PROJECTS_FILE = "projects.json";

function loadProjects(): Project[] {
  return readJsonFile<Project[]>(PROJECTS_FILE, []);
}

function saveProjects(projects: Project[]): void {
  writeJsonFile(PROJECTS_FILE, projects);
}

export function listProjects(orgId = "default"): Project[] {
  return loadProjects().filter((p) => p.orgId === orgId);
}

export function getProject(id: string): Project | undefined {
  return loadProjects().find((p) => p.id === id);
}

export function listProjectsByInstance(instanceId: string): Project[] {
  return loadProjects().filter((p) => p.instanceId === instanceId);
}

export interface CreateProjectResult {
  project: Project;
  instanceCreated: boolean;
}

export function createProject(input: CreateProjectInput): CreateProjectResult {
  const orgId = input.orgId ?? "default";
  const region = input.region ?? "local";
  const runtimeChoice = input.runtimeChoice ?? "new";
  let instanceCreated = false;
  let instanceId = input.instanceId;
  let deploymentMode: DeploymentMode;

  if (runtimeChoice === "new") {
    deploymentMode = "dedicated";
    const instance = createInstance({
      name: defaultInstanceName(input.name),
      orgId,
      deploymentMode: "dedicated",
      runtime: input.runtime,
    });
    instanceId = instance.id;
    instanceCreated = true;

    if (instance.runtimeTarget === "kubernetes") {
      provisionDedicatedInstance(instance);
    }
  } else {
    deploymentMode = "shared";
    if (!instanceId) {
      throw new Error("instanceId is required when adding to an existing instance");
    }
    const existing = getInstance(instanceId);
    if (!existing) {
      throw new Error(`Instance not found: ${instanceId}`);
    }
    if (existing.orgId !== orgId) {
      throw new Error("Instance belongs to a different organization");
    }
  }

  const now = new Date().toISOString();
  const project: Project = {
    id: generateId("proj"),
    name: input.name,
    orgId,
    instanceId: instanceId!,
    deploymentMode,
    region,
    createdAt: now,
    updatedAt: now,
  };

  const projects = loadProjects();
  projects.push(project);
  saveProjects(projects);

  if (deploymentMode === "shared") {
    const linked = getInstance(instanceId!);
    if (linked?.runtimeTarget === "kubernetes") {
      attachSharedProject(linked, project);
    }
  }

  return { project, instanceCreated };
}

export function deleteProject(id: string): boolean {
  const projects = loadProjects();
  const next = projects.filter((p) => p.id !== id);
  if (next.length === projects.length) return false;
  saveProjects(next);
  return true;
}

/** Test helper — replace entire project list. */
export function _setProjectsForTest(projects: Project[]): void {
  saveProjects(projects);
}

/** Test helper — clear projects file. */
export function _clearProjectsForTest(): void {
  saveProjects([]);
}

export async function listProjectsAsync(orgId?: string): Promise<Project[]> {
  const resolvedOrg = orgId ?? (await resolveStudioOrgId());
  if (!liorgEnabled()) {
    return listProjects(resolvedOrg);
  }
  return liorgListProjects(resolvedOrg);
}

export async function getProjectAsync(
  id: string,
  orgId?: string,
): Promise<Project | undefined> {
  if (!liorgEnabled()) {
    return getProject(id);
  }
  const resolvedOrg = orgId ?? (await resolveStudioOrgId());
  return liorgGetProject(resolvedOrg, id);
}

export async function listProjectsByInstanceAsync(
  instanceId: string,
  orgId?: string,
): Promise<Project[]> {
  const projects = await listProjectsAsync(orgId);
  return projects.filter((p) => p.instanceId === instanceId);
}

export async function createProjectAsync(
  input: CreateProjectInput,
): Promise<CreateProjectResult> {
  const orgId = input.orgId ?? studioOrgId();
  if (liorgEnabled()) {
    await requireEntitlement("project.create", orgId);
  }

  const region = input.region ?? "local";
  const runtimeChoice = input.runtimeChoice ?? "new";
  let instanceCreated = false;
  let instanceId = input.instanceId;
  let deploymentMode: DeploymentMode;

  if (runtimeChoice === "new") {
    deploymentMode = "dedicated";
    const instance = await createInstanceAsync({
      name: defaultInstanceName(input.name),
      orgId,
      deploymentMode: "dedicated",
      runtime: input.runtime,
    });
    instanceId = instance.id;
    instanceCreated = true;

    if (instance.runtimeTarget === "kubernetes") {
      provisionDedicatedInstance(instance);
    }
  } else {
    deploymentMode = "shared";
    if (!instanceId) {
      throw new Error("instanceId is required when adding to an existing instance");
    }
    const existing = await getInstanceAsync(instanceId, orgId);
    if (!existing) {
      throw new Error(`Instance not found: ${instanceId}`);
    }
    if (existing.orgId !== orgId) {
      throw new Error("Instance belongs to a different organization");
    }
  }

  if (liorgEnabled()) {
    const project = await liorgCreateProject(orgId, {
      name: input.name,
      instanceId: instanceId!,
      deploymentMode,
      region,
    });

    if (deploymentMode === "shared") {
      const linked = await getInstanceAsync(instanceId!, orgId);
      if (linked?.runtimeTarget === "kubernetes") {
        attachSharedProject(linked, project);
      }
    }

    return { project, instanceCreated };
  }

  return createProject(input);
}
