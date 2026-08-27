import type { CreateProjectInput, DeploymentMode, Project } from "./types";
import { notFound, redirect } from "next/navigation";
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
  AdminApiError,
  adminCreateProject,
  adminApiEnabled,
  adminDeleteProject,
  adminGetProject,
  adminListProjects,
  adminPatchProject,
} from "./librebase-admin-client";
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

  if (runtimeChoice === "new" || runtimeChoice === "vm") {
    deploymentMode = "dedicated";
    const instance = createInstance({
      name: defaultInstanceName(input.name),
      orgId,
      deploymentMode: "dedicated",
      runtime: input.runtime,
      hostId: runtimeChoice === "vm" ? input.hostId : undefined,
      memLimitMb: runtimeChoice === "vm" ? input.memLimitMb : undefined,
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
  if (!adminApiEnabled()) {
    return listProjects(resolvedOrg);
  }
  return adminListProjects(resolvedOrg);
}

export async function getProjectAsync(
  id: string,
  orgId?: string,
): Promise<Project | undefined> {
  if (!adminApiEnabled()) {
    return getProject(id);
  }
  const resolvedOrg = orgId ?? (await resolveStudioOrgId());
  return adminGetProject(resolvedOrg, id);
}

/**
 * Fetch a project for a page, mapping failures to the right user-facing
 * outcome instead of a dead-end 404:
 * - 401 (session missing/expired) → redirect to /login and come back,
 * - 403 (project belongs to another org) → notFound (do not leak existence),
 * - 404/unknown id → notFound,
 * - anything else (5xx, network) → rethrow so the error boundary can offer a retry.
 */
export async function requireProjectPage(projectId: string): Promise<Project> {
  let project: Project | undefined;
  try {
    project = await getProjectAsync(projectId);
  } catch (error) {
    if (error instanceof AdminApiError) {
      if (error.status === 401) {
        redirect(`/login?next=${encodeURIComponent(`/projects/${projectId}`)}`);
      }
      if (error.status === 403) {
        notFound();
      }
    }
    throw error;
  }
  if (!project) notFound();
  return project;
}

export function updateProject(
  id: string,
  patch: { name?: string },
): Project {
  const projects = loadProjects();
  const index = projects.findIndex((p) => p.id === id);
  if (index === -1) throw new Error(`Project not found: ${id}`);
  const name = patch.name?.trim();
  if (name !== undefined && !name) throw new Error("name is required");
  projects[index] = {
    ...projects[index],
    ...(name ? { name } : {}),
    updatedAt: new Date().toISOString(),
  };
  saveProjects(projects);
  return projects[index];
}

export async function updateProjectAsync(
  id: string,
  patch: { name?: string },
  orgId?: string,
): Promise<Project> {
  if (!adminApiEnabled()) {
    return updateProject(id, patch);
  }
  const resolvedOrg = orgId ?? (await resolveStudioOrgId());
  return adminPatchProject(resolvedOrg, id, { name: patch.name });
}

export async function deleteProjectAsync(
  id: string,
  orgId?: string,
): Promise<boolean> {
  if (!adminApiEnabled()) {
    return deleteProject(id);
  }
  const resolvedOrg = orgId ?? (await resolveStudioOrgId());
  await adminDeleteProject(resolvedOrg, id);
  return true;
}

export async function linkProjectToInstanceAsync(
  projectId: string,
  instanceId: string,
  orgId?: string,
): Promise<Project> {
  const resolvedOrg = orgId ?? (await resolveStudioOrgId());
  if (!adminApiEnabled()) {
    const projects = loadProjects();
    const index = projects.findIndex((p) => p.id === projectId);
    if (index === -1) throw new Error(`Project not found: ${projectId}`);
    const existing = getInstance(instanceId);
    if (!existing) throw new Error(`Instance not found: ${instanceId}`);
    if (existing.orgId !== resolvedOrg) {
      throw new Error("Instance belongs to a different organization");
    }
    projects[index] = {
      ...projects[index],
      instanceId,
      deploymentMode: "shared",
      updatedAt: new Date().toISOString(),
    };
    saveProjects(projects);
    return projects[index];
  }
  return adminPatchProject(resolvedOrg, projectId, { instanceId });
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
  if (adminApiEnabled()) {
    await requireEntitlement("project.create", orgId);
  }

  const region = input.region ?? "local";
  const runtimeChoice = input.runtimeChoice ?? "new";
  let instanceCreated = false;
  let instanceId = input.instanceId;
  let deploymentMode: DeploymentMode;

  if (runtimeChoice === "new" || runtimeChoice === "vm") {
    deploymentMode = "dedicated";
    const instance = await createInstanceAsync({
      name: defaultInstanceName(input.name),
      orgId,
      deploymentMode: "dedicated",
      runtime: input.runtime,
      hostId: runtimeChoice === "vm" ? input.hostId : undefined,
      memLimitMb: runtimeChoice === "vm" ? input.memLimitMb : undefined,
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

  if (adminApiEnabled()) {
    const project = await adminCreateProject(orgId, {
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
