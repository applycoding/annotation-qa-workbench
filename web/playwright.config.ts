// SPDX-License-Identifier: Apache-2.0

import { dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { defineConfig, devices } from "@playwright/test";

const rootDir = dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  testDir: "./tests",
  testMatch: "dashboard.spec.ts",
  fullyParallel: true,
  use: {
    baseURL: "http://127.0.0.1:4173",
    trace: "on-first-retry",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: {
    command: "npm run preview -- --host 127.0.0.1 --port 4173",
    cwd: rootDir,
    url: "http://127.0.0.1:4173/annotation-qa-workbench/",
    reuseExistingServer: false,
  },
});
