// SPDX-License-Identifier: Apache-2.0

import fs from "node:fs";
import path from "node:path";
import react from "@vitejs/plugin-react";
import { defineConfig, type Plugin } from "vite";

function requireCiReport(): Plugin {
  return {
    name: "require-ci-report",
    closeBundle() {
      const reportPath = path.resolve("dist", "report.json");
      if (!fs.existsSync(reportPath)) {
        throw new Error("production build missing report.json; copy the CI artifact first");
      }
      const report = JSON.parse(fs.readFileSync(reportPath, "utf8")) as {
        sample?: boolean;
      };
      if (report.sample === true) {
        throw new Error("production build must not ship sample_report.json as report.json");
      }
    },
  };
}

export default defineConfig({
  plugins: [react(), requireCiReport()],
  base: "/annotation-qa-workbench/",
  build: {
    outDir: "dist",
  },
});
