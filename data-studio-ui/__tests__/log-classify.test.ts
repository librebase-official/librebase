import { describe, expect, it } from "vitest";
import { classifyLogPath, filterLogLines } from "@/lib/log-classify";

describe("classifyLogPath", () => {
  it("maps known prefixes", () => {
    expect(classifyLogPath("/auth/v1/signup")).toBe("auth");
    expect(classifyLogPath("/rest/v1/items")).toBe("postgres");
    expect(classifyLogPath("/v1/sql")).toBe("postgres");
    expect(classifyLogPath("/storage/v1/bucket")).toBe("storage");
    expect(classifyLogPath("/functions/v1/hello")).toBe("edge");
    expect(classifyLogPath("/realtime/v1")).toBe("realtime");
    expect(classifyLogPath("/v1/health")).toBe("api");
    expect(classifyLogPath("/mystery")).toBe("other");
  });

  it("filters by kind and time", () => {
    const lines = [
      { raw: "a", path: "/auth/v1", ts: "2020-01-01T00:00:00.000Z" },
      { raw: "b", path: "/rest/v1/x", ts: new Date().toISOString() },
    ];
    expect(filterLogLines(lines, { kind: "auth" })).toHaveLength(1);
    expect(filterLogLines(lines, { kind: "postgres" })).toHaveLength(1);
    expect(filterLogLines(lines, { sinceMs: Date.now() - 60_000 })).toHaveLength(1);
  });
});
