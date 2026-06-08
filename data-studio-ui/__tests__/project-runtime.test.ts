import { describe, expect, it } from "vitest";
import { getApiUrl, getPostgresUrl } from "@/lib/project-runtime";
import type { Instance } from "@/lib/types";

describe("project-runtime url helpers", () => {
  const instance: Instance = {
    id: "inst_test",
    name: "test",
    orgId: "default",
    dataDir: "/tmp/test",
    ports: { api: 54320, postgres: 54322 },
    status: "stopped",
    deploymentMode: "dedicated",
    runtimeTarget: "local",
    createdAt: "",
    updatedAt: "",
  };

  it("builds API and postgres URLs from instance ports", () => {
    expect(getApiUrl(instance)).toBe("http://127.0.0.1:54320");
    expect(getPostgresUrl(instance)).toBe("postgresql://127.0.0.1:54322/librebase");
  });
});
