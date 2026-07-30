import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { afterEach, describe, expect, it } from "vitest";
import {
  parseAccessLogLine,
  readAccessLogTail,
  resolveAccessLogPath,
} from "@/lib/access-log";

const prev = {
  access: process.env.LIBREBASE_ACCESS_LOG,
  audit: process.env.LIP_REGISTRY_AUDIT_LOG,
  data: process.env.LI_DATA_DIR,
};

afterEach(() => {
  for (const [k, v] of Object.entries({
    LIBREBASE_ACCESS_LOG: prev.access,
    LIP_REGISTRY_AUDIT_LOG: prev.audit,
    LI_DATA_DIR: prev.data,
  })) {
    if (v === undefined) delete process.env[k];
    else process.env[k] = v;
  }
});

describe("access-log", () => {
  it("parses JSONL rows", () => {
    const row = parseAccessLogLine(
      '{"ts":"2026-07-30T00:00:00Z","method":"GET","path":"/rest/v1/x","status":200}',
    );
    expect(row.method).toBe("GET");
    expect(row.path).toBe("/rest/v1/x");
    expect(row.status).toBe(200);
  });

  it("tails configured file", () => {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), "lb-logs-"));
    const file = path.join(dir, "access.jsonl");
    fs.writeFileSync(
      file,
      [
        '{"ts":"t1","method":"GET","path":"/a","status":200}',
        '{"ts":"t2","method":"POST","path":"/b","status":201}',
      ].join("\n") + "\n",
    );
    process.env.LIBREBASE_ACCESS_LOG = file;
    expect(resolveAccessLogPath()).toBe(file);
    const lines = readAccessLogTail(file, 1);
    expect(lines).toHaveLength(1);
    expect(lines[0].path).toBe("/b");
  });
});
