import { defineConfig } from "@playwright/test";

export default defineConfig({
  webServer: {
    command: "npm run dev",
    port: 3000,
    timeout: 120000,
    reuseExistingServer: !process.env.CI
  },
  use: {
    baseURL: "http://127.0.0.1:3000"
  },
  testDir: "../tests/frontend"
});
