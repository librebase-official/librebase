import fs from "node:fs";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import {
  _clearInstancesForTest,
  createInstance,
  getInstance,
  listInstances,
} from "@/lib/instances-store";
import {
  resetTestStudioDataRoot,
  useTestStudioDataRoot,
} from "@/lib/studio-data-dir";

describe("instances-store", () => {
  beforeEach(() => {
    useTestStudioDataRoot();
    _clearInstancesForTest();
  });

  afterEach(() => {
    const root = process.env.LIBREBASE_STUDIO_DATA_DIR;
    resetTestStudioDataRoot();
    if (root) fs.rmSync(root, { recursive: true, force: true });
  });

  it("creates an instance with unique ports and data dir", () => {
    const a = createInstance({ name: "alpha-runtime" });
    const b = createInstance({ name: "beta-runtime" });

    expect(a.id).not.toBe(b.id);
    expect(a.ports.api).not.toBe(b.ports.api);
    expect(a.dataDir).not.toBe(b.dataDir);
    expect(fs.existsSync(a.dataDir)).toBe(true);
    expect(a.status).toBe("stopped");
    expect(a.orgId).toBe("default");
    expect(a.runtimeTarget).toBe("local");
  });

  it("creates kubernetes instance when runtime override set", () => {
    const inst = createInstance({ name: "k8s", runtime: "kubernetes" });
    expect(inst.runtimeTarget).toBe("kubernetes");
  });

  it("lists instances scoped to org", () => {
    createInstance({ name: "one", orgId: "default" });
    createInstance({ name: "two", orgId: "other-org" });

    expect(listInstances("default")).toHaveLength(1);
    expect(listInstances("other-org")).toHaveLength(1);
  });

  it("retrieves instance by id", () => {
    const created = createInstance({ name: "fetch-me" });
    expect(getInstance(created.id)?.name).toBe("fetch-me");
  });
});
