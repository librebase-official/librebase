import { spawnSync } from "node:child_process";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  _clearInstancesForTest,
  createInstance,
  getInstance,
} from "@/lib/instances-store";
import {
  attachSharedProject,
  deleteK8sInstance,
  getInstanceStatus,
  isClusterAvailable,
  provisionDedicatedInstance,
} from "@/lib/k8s-provisioner";
import {
  resetTestStudioDataRoot,
  useTestStudioDataRoot,
} from "@/lib/studio-data-dir";
import type { Project } from "@/lib/types";

vi.mock("node:child_process", () => ({
  spawnSync: vi.fn(),
}));

const mockSpawn = vi.mocked(spawnSync);

function kubectlOk(stdout = ""): ReturnType<typeof spawnSync> {
  return {
    status: 0,
    stdout,
    stderr: "",
    pid: 1,
    output: [null, stdout, ""],
    signal: null,
    error: undefined,
  } as ReturnType<typeof spawnSync>;
}

function kubectlFail(stderr: string): ReturnType<typeof spawnSync> {
  return {
    status: 1,
    stdout: "",
    stderr,
    pid: 1,
    output: [null, "", stderr],
    signal: null,
    error: undefined,
  } as ReturnType<typeof spawnSync>;
}

describe("k8s-provisioner", () => {
  beforeEach(() => {
    useTestStudioDataRoot();
    _clearInstancesForTest();
    mockSpawn.mockReset();
    delete process.env.KUBECONFIG;
  });

  afterEach(() => {
    resetTestStudioDataRoot();
  });

  it("reports cluster unavailable in degraded mode", () => {
    mockSpawn.mockReturnValue(kubectlFail("connection refused"));
    expect(isClusterAvailable()).toBe(false);

    const instance = createInstance({
      name: "k8s-test",
      runtime: "kubernetes",
    });
    const result = provisionDedicatedInstance(instance);
    expect(result.ok).toBe(false);
    expect(result.degraded).toBe(true);
    expect(result.message).toContain("unreachable");
    expect(getInstance(instance.id)?.k8sDegraded).toBe(true);
  });

  it("applies dedicated manifests when cluster is reachable", () => {
    mockSpawn.mockImplementation((_cmd, args) => {
      const joined = (args ?? []).join(" ");
      if (joined.includes("cluster-info")) return kubectlOk("Kubernetes control plane");
      if (joined.includes("apply")) return kubectlOk("namespace/librebase-inst created");
      return kubectlOk();
    });

    const instance = createInstance({
      name: "k8s-ok",
      runtime: "kubernetes",
    });
    const result = provisionDedicatedInstance(instance);
    expect(result.ok).toBe(true);
    expect(result.degraded).toBe(false);
    expect(getInstance(instance.id)?.k8sNamespace).toContain("librebase-inst-");
  });

  it("returns honest status when namespace missing", () => {
    mockSpawn.mockImplementation((_cmd, args) => {
      const joined = (args ?? []).join(" ");
      if (joined.includes("cluster-info")) return kubectlOk();
      if (joined.includes("get namespace")) return kubectlFail("NotFound");
      return kubectlOk();
    });

    const instance = createInstance({
      name: "k8s-status",
      runtime: "kubernetes",
    });
    const status = getInstanceStatus(instance.id);
    expect(status.degraded).toBe(false);
    expect(status.status).toBe("stopped");
    expect(status.message).toContain("Not provisioned");
  });

  it("maps running ready pod to running status", () => {
    const instance = createInstance({
      name: "k8s-running",
      runtime: "kubernetes",
    });

    mockSpawn.mockImplementation((_cmd, args) => {
      const joined = (args ?? []).join(" ");
      if (joined.includes("cluster-info")) return kubectlOk();
      if (joined.includes("get namespace")) return kubectlOk("librebase-inst-x");
      if (joined.includes("jsonpath")) return kubectlOk("Running,True");
      return kubectlOk();
    });

    const status = getInstanceStatus(instance.id);
    expect(status.status).toBe("running");
    expect(status.ready).toBe(true);
  });

  it("attachSharedProject requires shared deployment mode", () => {
    const instance = createInstance({
      name: "dedicated-only",
      runtime: "kubernetes",
      deploymentMode: "dedicated",
    });
    const project: Project = {
      id: "proj_1",
      name: "P",
      orgId: "default",
      instanceId: instance.id,
      deploymentMode: "shared",
      region: "local",
      createdAt: "",
      updatedAt: "",
    };
    const result = attachSharedProject(instance, project);
    expect(result.ok).toBe(false);
    expect(result.message).toContain("shared");
  });

  it("deleteK8sInstance removes dedicated namespace", () => {
    const instance = createInstance({
      name: "to-delete",
      runtime: "kubernetes",
      deploymentMode: "dedicated",
    });

    mockSpawn.mockImplementation((_cmd, args) => {
      const joined = (args ?? []).join(" ");
      if (joined.includes("cluster-info")) return kubectlOk();
      if (joined.includes("delete namespace")) return kubectlOk("deleted");
      return kubectlOk();
    });

    const result = deleteK8sInstance(instance.id);
    expect(result.ok).toBe(true);
    expect(result.message).toContain("Deleted namespace");
  });
});
