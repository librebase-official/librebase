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

function mockPortsOpen(): void {
  vi.mocked(net.createConnection).mockImplementation(() => {
    const socket = {
      setTimeout: vi.fn(),
      destroy: vi.fn(),
      on: (event: string, cb: () => void) => {
        if (event === "connect") {
          queueMicrotask(cb);
        }
      },
    };
    return socket as unknown as ReturnType<typeof net.createConnection>;
  });
}

describe("probeInstanceDb dev runtime", () => {
  const instance: Instance = {
    id: "inst_dev_test",
    name: "dev-test",
    orgId: "default",
    dataDir: "/tmp/dev-test",
    ports: { api: 54320, postgres: 54322 },
    status: "stopped",
    deploymentMode: "dedicated",
    runtimeTarget: "local",
    createdAt: "2026-01-01T00:00:00.000Z",
    updatedAt: "2026-01-01T00:00:00.000Z",
  };

  beforeEach(() => {
    useTestStudioDataRoot();
    _setInstancesForTest([instance]);
    mockPortsOpen();
  });

  afterEach(() => {
    vi.clearAllMocks();
    const root = process.env.LIBREBASE_STUDIO_DATA_DIR;
    resetTestStudioDataRoot();
    if (root) fs.rmSync(root, { recursive: true, force: true });
  });

  it("reports dev runtime mode when engine returns running dev status", async () => {
    vi.mocked(spawnSync).mockReturnValue({
      status: 0,
      stdout: JSON.stringify({
        status: "running",
        degraded: true,
        runtime_mode: "dev",
        message: "Dev runtime — ports reachable (not production lidb)",
        running: true,
        api_reachable: true,
        postgres_reachable: true,
      }),
      stderr: "",
    } as ReturnType<typeof spawnSync>);

    const result = await probeInstanceDb(instance);

    expect(result.runtimeMode).toBe("dev");
    expect(result.status).toBe("running");
    expect(result.reachable).toBe(true);
    expect(result.degraded).toBe(true);
    expect(result.message).toContain("Dev runtime");
  });
});
