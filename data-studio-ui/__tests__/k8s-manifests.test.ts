import { describe, expect, it } from "vitest";
import {
  buildDedicatedManifests,
  buildSharedInstanceManifests,
  buildSharedProjectConfigMap,
  dedicatedNamespace,
  instanceLabels,
  sharedNamespace,
} from "@/lib/k8s-manifests";
import type { Instance, Project } from "@/lib/types";

const baseInstance: Instance = {
  id: "inst_abc123",
  name: "demo-runtime",
  orgId: "default",
  dataDir: "/tmp/demo",
  ports: { api: 54320, postgres: 54322 },
  status: "stopped",
  deploymentMode: "dedicated",
  runtimeTarget: "kubernetes",
  createdAt: "2026-01-01T00:00:00.000Z",
  updatedAt: "2026-01-01T00:00:00.000Z",
};

const baseProject: Project = {
  id: "proj_xyz",
  name: "Demo",
  orgId: "default",
  instanceId: "inst_abc123",
  deploymentMode: "shared",
  region: "local",
  createdAt: "2026-01-01T00:00:00.000Z",
  updatedAt: "2026-01-01T00:00:00.000Z",
};

describe("k8s-manifests", () => {
  it("builds dedicated namespace per instance id", () => {
    expect(dedicatedNamespace("inst_abc123")).toBe("librebase-inst-inst_abc123");
  });

  it("builds shared namespace from org id", () => {
    expect(sharedNamespace("default")).toBe("librebase-shared-default");
    expect(sharedNamespace("Acme_Corp")).toBe("librebase-shared-acme-corp");
  });

  it("includes required librebase labels", () => {
    const labels = instanceLabels(baseInstance);
    expect(labels["librebase.io/org"]).toBe("default");
    expect(labels["librebase.io/instance"]).toBe("inst_abc123");
    expect(labels["librebase.io/deployment-mode"]).toBe("dedicated");
  });

  it("generates dedicated multi-doc manifest with probes and PVC", () => {
    const yaml = buildDedicatedManifests({ instance: baseInstance });
    expect(yaml).toContain("kind: Namespace");
    expect(yaml).toContain("name: librebase-inst-inst_abc123");
    expect(yaml).toContain("kind: PersistentVolumeClaim");
    expect(yaml).toContain("lidb_engine.py");
    expect(yaml).toContain("kind: Service");
    expect(yaml).toContain('librebase.io/deployment-mode: "dedicated"');
    expect(yaml).toContain("librebase/lidb-runtime:dev");
    expect(yaml).toContain('LIDB_RUNTIME_MODE: "dev"');
  });

  it("generates shared instance base manifests", () => {
    const sharedInstance = { ...baseInstance, deploymentMode: "shared" as const };
    const yaml = buildSharedInstanceManifests({ instance: sharedInstance });
    expect(yaml).toContain("librebase-shared-default");
    expect(yaml).toContain("librebase-runtime-inst_abc123");
    expect(yaml).toContain("librebase-data-inst_abc123");
  });

  it("generates shared project ConfigMap", () => {
    const sharedInstance = { ...baseInstance, deploymentMode: "shared" as const };
    const yaml = buildSharedProjectConfigMap({
      instance: sharedInstance,
      project: baseProject,
    });
    expect(yaml).toContain("librebase-project-proj_xyz");
    expect(yaml).toContain("LIBREBASE_SCHEMA_NAMESPACE");
    expect(yaml).toContain('librebase.io/project: "proj_xyz"');
  });
});
