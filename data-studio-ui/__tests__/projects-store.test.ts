import fs from "node:fs";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import {
  _clearInstancesForTest,
  createInstance,
  listInstances,
} from "@/lib/instances-store";
import {
  _clearProjectsForTest,
  createProject,
  getProject,
  listProjects,
  listProjectsByInstance,
} from "@/lib/projects-store";
import {
  resetTestStudioDataRoot,
  useTestStudioDataRoot,
} from "@/lib/studio-data-dir";

describe("projects-store", () => {
  beforeEach(() => {
    useTestStudioDataRoot();
    _clearInstancesForTest();
    _clearProjectsForTest();
  });

  afterEach(() => {
    const root = process.env.LIBREBASE_STUDIO_DATA_DIR;
    resetTestStudioDataRoot();
    if (root) fs.rmSync(root, { recursive: true, force: true });
  });

  it("dedicated project provisions a new instance (1:1)", () => {
    const { project, instanceCreated } = createProject({
      name: "Alpha",
      runtimeChoice: "new",
    });

    expect(instanceCreated).toBe(true);
    expect(project.deploymentMode).toBe("dedicated");
    expect(listInstances()).toHaveLength(1);
    expect(getProject(project.id)?.instanceId).toBe(listInstances()[0].id);
  });

  it("shared project attaches to an existing instance without new provisioning", () => {
    const host = createInstance({ name: "shared-host", deploymentMode: "dedicated" });

    const first = createProject({
      name: "Beta",
      runtimeChoice: "existing",
      instanceId: host.id,
    });
    const second = createProject({
      name: "Gamma",
      runtimeChoice: "existing",
      instanceId: host.id,
    });

    expect(first.instanceCreated).toBe(false);
    expect(second.instanceCreated).toBe(false);
    expect(first.project.deploymentMode).toBe("shared");
    expect(second.project.deploymentMode).toBe("shared");
    expect(first.project.instanceId).toBe(host.id);
    expect(second.project.instanceId).toBe(host.id);
    expect(listInstances()).toHaveLength(1);
    expect(listProjects()).toHaveLength(2);
    expect(listProjectsByInstance(host.id)).toHaveLength(2);
  });

  it("rejects shared create when instanceId is missing", () => {
    expect(() =>
      createProject({ name: "Bad", runtimeChoice: "existing" }),
    ).toThrow(/instanceId is required/);
  });
});
