import { describe, expect, it } from "vitest";
import { slugify } from "@/lib/json-store";

describe("json-store slugify", () => {
  it("normalizes names to lowercase hyphenated slugs", () => {
    expect(slugify("  My Cool Project!!  ")).toBe("my-cool-project");
    expect(slugify("---hello---")).toBe("hello");
  });

  it("truncates long slugs and returns empty for non-alphanumeric input", () => {
    expect(slugify("a".repeat(60))).toHaveLength(48);
    expect(slugify("!!!")).toBe("");
  });
});
