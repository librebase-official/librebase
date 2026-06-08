import fs from "node:fs";
import path from "node:path";
import { ensureStudioDataRoot, studioFile } from "./studio-data-dir";

export function readJsonFile<T>(filename: string, fallback: T): T {
  ensureStudioDataRoot();
  const filePath = studioFile(filename);
  if (!fs.existsSync(filePath)) {
    return fallback;
  }
  try {
    const raw = fs.readFileSync(filePath, "utf8");
    return JSON.parse(raw) as T;
  } catch {
    return fallback;
  }
}

export function writeJsonFile<T>(filename: string, data: T): void {
  ensureStudioDataRoot();
  const filePath = studioFile(filename);
  fs.writeFileSync(filePath, JSON.stringify(data, null, 2), "utf8");
}

export function generateId(prefix: string): string {
  const stamp = Date.now().toString(36);
  const rand = Math.random().toString(36).slice(2, 8);
  return `${prefix}_${stamp}_${rand}`;
}

export function slugify(value: string): string {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 48);
}

export function instanceDataDir(instanceId: string): string {
  return path.join(ensureStudioDataRoot(), "instances", instanceId);
}
