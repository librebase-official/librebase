import { afterEach, describe, expect, it } from "vitest";
import { getHarnessMode, getLibrebaseRuntime, resolveRuntimeTarget } from "@/lib/runtime-env";

describe("runtime-env", () => {
  afterEach(() => {
    delete process.env.LIBREBASE_RUNTIME;
    delete process.env.LIBREBASE_HARNESS;
    delete process.env.NEXT_PUBLIC_HARNESS;
  });

  it("defaults to local when unset", () => {
    expect(getLibrebaseRuntime()).toBe("local");
  });

  it("reads kubernetes from env", () => {
    process.env.LIBREBASE_RUNTIME = "kubernetes";
    expect(getLibrebaseRuntime()).toBe("kubernetes");
  });

  it("reads licontainer from env", () => {
    process.env.LIBREBASE_RUNTIME = "licontainer";
    expect(getLibrebaseRuntime()).toBe("licontainer");
  });

  it("resolveRuntimeTarget prefers explicit override", () => {
    process.env.LIBREBASE_RUNTIME = "kubernetes";
    expect(resolveRuntimeTarget("local")).toBe("local");
    expect(resolveRuntimeTarget()).toBe("kubernetes");
  });

  it("defaults harness to saas when unset", () => {
    expect(getHarnessMode()).toBe("saas");
  });

  it("reads oss harness from env", () => {
    process.env.LIBREBASE_HARNESS = "oss";
    expect(getHarnessMode()).toBe("oss");
  });
});
