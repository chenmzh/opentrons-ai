import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  fullyParallel: false,
  workers: 1,
  use: {
    baseURL: "http://127.0.0.1:8091",
    viewport: { width: 1440, height: 1000 },
    trace: "retain-on-failure",
  },
  webServer: {
    command:
      "OT2_DATA_DIR=../.local/browser-tests ../.venv/bin/python -m opentrons_ai serve --port 8091",
    url: "http://127.0.0.1:8091",
    reuseExistingServer: false,
  },
});
