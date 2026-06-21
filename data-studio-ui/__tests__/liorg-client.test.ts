import { afterEach, describe, expect, it, vi } from "vitest";
import {
  liorgBaseUrl,
  liorgCheckEntitlement,
  liorgEnabled,
  liorgHealth,
} from "@/lib/liorg-client";

describe("liorg-client", () => {
  const originalEnv = { ...process.env };

  afterEach(() => {
    process.env = { ...originalEnv };
    vi.restoreAllMocks();
  });

  it("liorgEnabled is false without LIBREBASE_ORG_URL", () => {
    delete process.env.LIBREBASE_ORG_URL;
    expect(liorgEnabled()).toBe(false);
  });

  it("liorgBaseUrl defaults to local control plane port", () => {
    delete process.env.LIBREBASE_ORG_URL;
    expect(liorgBaseUrl()).toBe("http://127.0.0.1:54330");
  });

  it("liorgHealth returns true on ok response", async () => {
    process.env.LIBREBASE_ORG_URL = "http://127.0.0.1:54330";
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: true }),
    );
    await expect(liorgHealth()).resolves.toBe(true);
  });

  it("liorgCheckEntitlement parses enabled flag", async () => {
    process.env.LIBREBASE_ORG_URL = "http://127.0.0.1:54330";
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ enabled: true, status: "allowed", code: 1 }),
      }),
    );
    await expect(liorgCheckEntitlement("org-a", "project.create")).resolves.toEqual({
      enabled: true,
      status: "allowed",
      code: 1,
    });
  });
});
