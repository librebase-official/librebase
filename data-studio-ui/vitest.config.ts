import path from "node:path";
import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    environment: "node",
    include: ["__tests__/**/*.test.ts"],
    env: {
      // OSS harness: k8s-provisioner tests expect kubectl paths, not SaaS Hetzner gate.
      LIBREBASE_HARNESS: "oss",
    },
    coverage: {
      provider: "v8",
      include: ["lib/**"],
      reporter: ["text", "text-summary"],
      thresholds: {
        lines: 30,
      },
    },
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "."),
    },
  },
});
