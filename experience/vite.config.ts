import { configDefaults, defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/reviews": "http://localhost:8100",
      "/health": "http://localhost:8100",
    },
  },
  test: {
    exclude: [...configDefaults.exclude, "scripts/contracts/*.test.mjs"],
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test-setup.ts"],
  },
});
