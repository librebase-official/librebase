import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";

vi.mock("node:child_process", () => ({
  spawnSync: vi.fn(),
}));

vi.mock("@/lib/instances-store", () => ({
  getInstance: vi.fn((id: string) =>
    id === "inst_lc1"
      ? {
          id: "inst_lc1",
          name: "licontainer-demo",
          orgId: "default",
          dataDir: "/tmp/lc",
          ports: { api: 54320, postgres: 54322 },
          status: "stopped",
          deploymentMode: "dedicated",
          runtimeTarget: "licontainer",
          createdAt: "2026-01-01T00:00:00.000Z",
          updatedAt: "2026-01-01T00:00:00.000Z",
        }
      : undefined,
  ),
  updateInstance: vi.fn(),
}));

import { spawnSync } from "node:child_process";
import {
  getLicontainerInstanceStatus,
  isLicontainerAvailable,
  provisionLicontainerInstance,
} from "@/lib/licontainer-provisioner";
import type { Instance } from "@/lib/types";

const mockSpawn = vi.mocked(spawnSync);

const baseInstance: Instance = {
  id: "inst_lc1",
  name: "licontainer-demo",
  orgId: "default",
  dataDir: "/tmp/lc",
  ports: { api: 54320, postgres: 54322 },
  status: "stopped",
  deploymentMode: "dedicated",
  runtimeTarget: "licontainer",
  createdAt: "2026-01-01T00:00:00.000Z",
  updatedAt: "2026-01-01T00:00:00.000Z",
};

describe("licontainer-provisioner", () => {
  beforeEach(() => {
    mockSpawn.mockReset();
  });

  afterEach(() => {
    delete process.env.LI_CONTAINER_SOCKET;
  });

  it("reports degraded when daemon unreachable", () => {
    mockSpawn.mockReturnValue({
      status: 1,
      stdout: "",
      stderr: "no socket",
      pid: 0,
      output: ["", "", ""],
      signal: null,
    } as ReturnType<typeof spawnSync>);

    expect(isLicontainerAvailable()).toBe(false);

    const result = provisionLicontainerInstance(baseInstance);
    expect(result.ok).toBe(false);
    expect(result.degraded).toBe(true);
    expect(result.message).toContain("unreachable");
  });

  it("provisions when daemon reachable and lictl succeeds", () => {
    mockSpawn
      .mockReturnValueOnce({
        status: 0,
        stdout: "",
        stderr: "",
        pid: 0,
        output: ["", "", ""],
        signal: null,
      } as ReturnType<typeof spawnSync>)
      .mockReturnValueOnce({
        status: 0,
        stdout: "Pulled",
        stderr: "",
        pid: 0,
        output: ["", "", ""],
        signal: null,
      } as ReturnType<typeof spawnSync>)
      .mockReturnValueOnce({
        status: 0,
        stdout: "Started container",
        stderr: "",
        pid: 0,
        output: ["", "", ""],
        signal: null,
      } as ReturnType<typeof spawnSync>);

    const result = provisionLicontainerInstance(baseInstance);
    expect(result.ok).toBe(true);
    expect(result.degraded).toBe(false);
  });

  it("getLicontainerInstanceStatus parses ps output", () => {
    mockSpawn
      .mockReturnValueOnce({
        status: 0,
        stdout: "",
        stderr: "",
        pid: 0,
        output: ["", "", ""],
        signal: null,
      } as ReturnType<typeof spawnSync>)
      .mockReturnValueOnce({
        status: 0,
        stdout: "librebase-inst_lc1 running",
        stderr: "",
        pid: 0,
        output: ["", "", ""],
        signal: null,
      } as ReturnType<typeof spawnSync>);

    const status = getLicontainerInstanceStatus("inst_lc1");
    expect(status.status).toBe("running");
    expect(status.degraded).toBe(false);
  });
});
