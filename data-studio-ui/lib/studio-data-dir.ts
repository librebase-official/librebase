import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const STUDIO_DIR_NAME = "studio";

/** Platform-specific Librebase Studio persistence root (~/.local/share/librebase/studio on Unix). */
export function getStudioDataRoot(): string {
  if (process.env.LIBREBASE_STUDIO_DATA_DIR) {
    return process.env.LIBREBASE_STUDIO_DATA_DIR;
  }

  const home = os.homedir();
  if (process.platform === "win32") {
    const localAppData =
      process.env.LOCALAPPDATA ?? path.join(home, "AppData", "Local");
    return path.join(localAppData, "librebase", STUDIO_DIR_NAME);
  }

  return path.join(home, ".local", "share", "librebase", STUDIO_DIR_NAME);
}

export function ensureStudioDataRoot(): string {
  const root = getStudioDataRoot();
  fs.mkdirSync(root, { recursive: true });
  return root;
}

export function studioFile(name: string): string {
  return path.join(getStudioDataRoot(), name);
}

/** Isolated data dir for test runs — never touches user studio state. */
export function useTestStudioDataRoot(): string {
  const root = path.join(
    os.tmpdir(),
    "librebase-studio-test",
    `run-${Date.now()}-${Math.random().toString(36).slice(2)}`,
  );
  fs.mkdirSync(root, { recursive: true });
  process.env.LIBREBASE_STUDIO_DATA_DIR = root;
  return root;
}

export function resetTestStudioDataRoot(): void {
  delete process.env.LIBREBASE_STUDIO_DATA_DIR;
}
