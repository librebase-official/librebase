import { afterEach, describe, expect, it } from "vitest";
import { getLibrebaseRuntime, resolveRuntimeTarget } from "@/lib/runtime-env";

describe("runtime-env", () => {
  afterEach(() => {
    delete process.env.LIBREBASE_RUNTIME;
  });

  it("defaults to local when unset", () => {
    expect(getLibrebaseRuntime()).toBe("local");
  });

  it("reads kubernetes from env", () => {
    process.env.LIBREBASE_RUNTIME = "kubernetes";
    expect(getLibrebaseRuntime()).toBe("kubernetes");
  });

  it("resolveRuntimeTarget prefers explicit override", () => {
    process.env.LIBREBASE_RUNTIME = "kubernetes";
    expect(resolveRuntimeTarget("local")).toBe("local");
    expect(resolveRuntimeTarget()).toBe("kubernetes");
  });
});
