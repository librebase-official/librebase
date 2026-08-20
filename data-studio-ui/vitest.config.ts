import path from "node:path";
import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    environment: "node",
    include: ["__tests__/**/*.test.ts"],
    env: {
      LIBREBASE_ALLOW_LOCAL: "1",
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
