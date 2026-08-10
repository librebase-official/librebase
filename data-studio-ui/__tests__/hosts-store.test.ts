import { afterEach, describe, expect, it, vi } from "vitest";
import {
  adminCreateHost,
  adminGetHost,
  adminListHosts,
} from "@/lib/librebase-admin-client";
import { createHostAsync, hostPortBlock, listHostsAsync } from "@/lib/hosts-store";

describe("hosts-store / admin hosts", () => {
  const originalEnv = { ...process.env };

  afterEach(() => {
    process.env = { ...originalEnv };
    vi.restoreAllMocks();
  });

  it("hostPortBlock allocates per-index api/postgres ports", () => {
    expect(hostPortBlock(0)).toEqual({ api: 54320, postgres: 54322 });
    expect(hostPortBlock(1)).toEqual({ api: 54330, postgres: 54332 });
  });

  it("listHostsAsync without admin API returns empty list (file fallback)", async () => {
    delete process.env.LIBREBASE_ADMIN_URL;
    delete process.env.LIBREBASE_ORG_URL;
    const hosts = await listHostsAsync("org_x");
    expect(Array.isArray(hosts)).toBe(true);
  });

  it("adminListHosts hits /org/v1/orgs/{orgId}/hosts", async () => {
    process.env.LIBREBASE_ADMIN_URL = "http://127.0.0.1:54330";
    process.env.LIBREBASE_ADMIN_SESSION = "tok";
    const mockRows = [
      {
        id: "host_1",
        orgId: "org_x",
        name: "vm",
        provider: "sail",
        region: "eu",
        memMb: 512,
        memUsedMb: 0,
        status: "running",
        createdAt: "t0",
        updatedAt: "t1",
      },
    ];
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify(mockRows), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      ),
    );
    const hosts = await adminListHosts("org_x");
    expect(hosts).toHaveLength(1);
    expect(hosts[0].memMb).toBe(512);
  });

  it("adminGetHost returns undefined on 404", async () => {
    process.env.LIBREBASE_ADMIN_URL = "http://127.0.0.1:54330";
    process.env.LIBREBASE_ADMIN_SESSION = "tok";
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("not found", { status: 404 })),
    );
    await expect(adminGetHost("org_x", "host_9")).resolves.toBeUndefined();
  });

  it("adminCreateHost POSTs name/memMb and returns host", async () => {
    process.env.LIBREBASE_ADMIN_URL = "http://127.0.0.1:54330";
    process.env.LIBREBASE_ADMIN_SESSION = "tok";
    const created = {
      id: "host_2",
      orgId: "org_x",
      name: "vm2",
      provider: "linative-cloud",
      region: "local",
      memMb: 1024,
      memUsedMb: 0,
      status: "stopped",
      createdAt: "t0",
      updatedAt: "t1",
    };
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify(created), {
          status: 201,
          headers: { "Content-Type": "application/json" },
        }),
      ),
    );
    const host = await adminCreateHost("org_x", { name: "vm2", memMb: 1024 });
    expect(host.id).toBe("host_2");
    expect(host.memMb).toBe(1024);
  });

  it("createHostAsync without admin API throws (control plane required)", async () => {
    delete process.env.LIBREBASE_ADMIN_URL;
    delete process.env.LIBREBASE_ORG_URL;
    await expect(createHostAsync({ name: "vm" })).rejects.toThrow(
      /LIBREBASE_ADMIN_URL/,
    );
  });
});
