import { afterEach, describe, expect, it } from "vitest";
import { getLibrebaseRuntime, isLocalRuntimeAllowed, resolveRuntimeTarget } from "@/lib/runtime-env";

describe("runtime-env", () => {
  afterEach(() => {
    delete process.env.LIBREBASE_RUNTIME;
    process.env.LIBREBASE_ALLOW_LOCAL = "1";
  });

  it("defaults to local when unset and localhost is allowed", () => {
    expect(getLibrebaseRuntime()).toBe("local");
  });

  it("defaults to kubernetes when localhost is disabled", () => {
    delete process.env.LIBREBASE_ALLOW_LOCAL;
    expect(getLibrebaseRuntime()).toBe("kubernetes");
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

  it("refuses explicit local when localhost is disabled", () => {
    delete process.env.LIBREBASE_ALLOW_LOCAL;
    process.env.LIBREBASE_RUNTIME = "kubernetes";
    expect(isLocalRuntimeAllowed()).toBe(false);
    expect(resolveRuntimeTarget("local")).toBe("kubernetes");
  });
});
