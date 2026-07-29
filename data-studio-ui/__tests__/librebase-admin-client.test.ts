import { afterEach, describe, expect, it, vi } from "vitest";
import {
  adminApiEnabled,
  adminBaseUrl,
  adminCheckEntitlement,
  adminHealth,
} from "@/lib/librebase-admin-client";

describe("librebase-admin-client", () => {
  const originalEnv = { ...process.env };

  afterEach(() => {
    process.env = { ...originalEnv };
    vi.restoreAllMocks();
  });

  it("adminApiEnabled is false without LIBREBASE_ADMIN_URL", () => {
    delete process.env.LIBREBASE_ADMIN_URL;
    delete process.env.LIBREBASE_ORG_URL;
    expect(adminApiEnabled()).toBe(false);
  });

  it("adminApiEnabled accepts deprecated LIBREBASE_ORG_URL", () => {
    process.env.LIBREBASE_ORG_URL = "http://127.0.0.1:54330";
    expect(adminApiEnabled()).toBe(true);
  });

  it("adminBaseUrl defaults to local admin port", () => {
    delete process.env.LIBREBASE_ADMIN_URL;
    delete process.env.LIBREBASE_ORG_URL;
    expect(adminBaseUrl()).toBe("http://127.0.0.1:54330");
  });

  it("adminHealth returns true on ok response", async () => {
    process.env.LIBREBASE_ADMIN_URL = "http://127.0.0.1:54330";
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true }));
    await expect(adminHealth()).resolves.toBe(true);
  });

  it("adminCheckEntitlement parses enabled flag", async () => {
    process.env.LIBREBASE_ADMIN_URL = "http://127.0.0.1:54330";
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ enabled: true, status: "allowed", code: 1 }),
      }),
    );
    await expect(adminCheckEntitlement("org-a", "project.create")).resolves.toEqual({
      enabled: true,
      status: "allowed",
      code: 1,
    });
  });
});
