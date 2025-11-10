/// <reference types="vitest" />
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";

// https://vitejs.dev/config/
export default defineConfig(({ command, mode }) => {
  // Only enable the PWA plugin for production builds. During local development
  // the service worker can interfere with API requests (conditional GETs and
  // 304 responses), causing empty responses and JSON parse failures.
  const isProd = mode === "production";

  return {
    plugins: [
      react(),
      // PWA plugin temporarily disabled to fix build issues
    ],
    server: {
      port: 3000,
      proxy: {
        "/api": {
          // Docker-compose publishes the api container's internal 8000 -> host 8001
          // so proxy to localhost:8001 on the host
          target: "http://localhost:8001",
          changeOrigin: true,
        },
      },
    },
    test: {
      globals: true,
      environment: "jsdom",
      setupFiles: "./src/test/setup.ts",
      coverage: {
        provider: "v8",
        reporter: ["text", "json", "html"],
        exclude: [
          "node_modules/",
          "src/test/",
          "**/*.d.ts",
          "**/*.config.*",
          "coverage/",
          "dist/",
        ],
        thresholds: {
          global: {
            branches: 80,
            functions: 80,
            lines: 80,
            statements: 80,
          },
        },
      },
    },
  };
});
