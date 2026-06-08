import fs from "node:fs";
import { spawnSync } from "node:child_process";
import net from "node:net";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { _clearInstancesForTest, _setInstancesForTest } from "@/lib/instances-store";
import { probeInstanceDb } from "@/lib/project-runtime";
import {
  resetTestStudioDataRoot,
  useTestStudioDataRoot,
} from "@/lib/studio-data-dir";
import type { Instance } from "@/lib/types";

vi.mock("node:child_process", () => ({
  spawnSync: vi.fn(),
}));

vi.mock("node:net", () => ({
  default: {
    createConnection: vi.fn(),
  },
}));

function mockPortClosed(): void {
  vi.mocked(net.createConnection).mockImplementation(() => {
    const socket = {
      setTimeout: vi.fn(),
      destroy: vi.fn(),
      on: (event: string, cb: () => void) => {
        if (event === "error") {
          queueMicrotask(cb);
        }
      },
    };
    return socket as unknown as ReturnType<typeof net.createConnection>;
  });
}

describe("probeInstanceDb degraded path", () => {
  const instance: Instance = {
    id: "inst_probe_test",
    name: "probe-test",
    orgId: "default",
    dataDir: "/tmp/probe-test",
    ports: { api: 54320, postgres: 54322 },
    status: "running",
    deploymentMode: "dedicated",
    createdAt: "2026-01-01T00:00:00.000Z",
    updatedAt: "2026-01-01T00:00:00.000Z",
  };

  beforeEach(() => {
    useTestStudioDataRoot();
    _setInstancesForTest([instance]);
    mockPortClosed();
  });

  afterEach(() => {
    vi.clearAllMocks();
    const root = process.env.LIBREBASE_STUDIO_DATA_DIR;
    resetTestStudioDataRoot();
    if (root) fs.rmSync(root, { recursive: true, force: true });
  });

  it("marks instance stopped when engine is degraded and API port is closed", async () => {
    vi.mocked(spawnSync).mockReturnValue({
      status: 0,
      stdout: JSON.stringify({
        status: "stopped",
        degraded: true,
        message: "Runtime unavailable (degraded mode)",
      }),
      stderr: "",
    } as ReturnType<typeof spawnSync>);

    const result = await probeInstanceDb(instance);

    expect(result.degraded).toBe(true);
    expect(result.reachable).toBe(false);
    expect(result.status).toBe("stopped");
    expect(result.message).toContain("degraded");
  });

  it("marks instance stopped when engine fails and API port is closed", async () => {
    vi.mocked(spawnSync).mockReturnValue({
      status: 1,
      stdout: "",
      stderr: "lidb engine unavailable",
    } as ReturnType<typeof spawnSync>);

    const result = await probeInstanceDb(instance);

    expect(result.degraded).toBe(true);
    expect(result.reachable).toBe(false);
    expect(result.status).toBe("stopped");
    expect(result.message).toContain("lidb engine unavailable");
  });
});
