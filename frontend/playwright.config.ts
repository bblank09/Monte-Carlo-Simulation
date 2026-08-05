import { defineConfig, devices } from "@playwright/test";

// The production build (frontend/dist) is served directly by the FastAPI
// backend on a single origin -- the same setup used in the real Docker
// deployment (see backend/app/main.py's static-serving block) -- rather than
// through Vite's dev server. Run `npm run build` before `npm run test:e2e`.
//
// Timeout is generous (90s) because the real SEC Open Data API backing
// /api/simulate and /api/funds can take 30-45s on a cold cache.
export default defineConfig({
  testDir: "./e2e",
  timeout: 90_000,
  fullyParallel: false,
  retries: 2,
  reporter: "list",
  use: {
    baseURL: "http://127.0.0.1:8001",
    trace: "retain-on-failure"
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] }
    }
  ],
  webServer: {
    command: "python3 -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8001",
    url: "http://127.0.0.1:8001/api/health",
    reuseExistingServer: true,
    cwd: "..",
    timeout: 30_000
  }
});
