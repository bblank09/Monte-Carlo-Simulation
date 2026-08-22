import { test, expect } from "@playwright/test";

test.setTimeout(120_000);

test("exposes only supported assumptions and an accessible goals editor", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("button", { name: "Portfolio", exact: true })).toBeVisible();

  await expect(async () => {
    await page.getByText("Load an example portfolio").click();
    await expect(page.getByText("100%", { exact: true })).toBeVisible();
  }).toPass({ timeout: 60_000 });

  await page.getByRole("button", { name: /continue to assumptions/i }).click();

  const cashflowOptions = await page.getByLabel("Cashflow mode").locator("option").allTextContents();
  expect(cashflowOptions).not.toContain("Rolling average spending rule");
  expect(cashflowOptions).not.toContain("Geometric spending rule");
  expect(cashflowOptions).not.toContain("Withdraw based on life expectancy");
  await expect(page.getByText(/rebalancing is available for statistical normal returns/i)).toBeVisible();

  const advancedToggle = page.getByRole("button", { name: /advanced settings/i });
  await advancedToggle.press("Enter");
  await expect(page.getByLabel("Number of Simulation Paths")).toBeVisible();

  await page.getByLabel("Enable named goals and glide path").check();
  await expect(page.getByLabel("Goal purpose 1")).toBeVisible();
  await expect(page.getByLabel("Years to retirement")).toBeVisible();
  await expect(page.getByLabel("Glide path years")).toBeVisible();
});

test("retries fund loading instead of submitting an empty simulation", async ({ page }) => {
  let attempts = 0;
  await page.route("**/api/funds", async (route) => {
    attempts += 1;
    if (attempts === 1) {
      await route.fulfill({
        status: 503,
        contentType: "application/json",
        body: JSON.stringify({ detail: "cache unavailable", code: "FUND_UNIVERSE_CACHE_MISSING" }),
      });
      return;
    }
    await route.continue();
  });

  await page.goto("/");
  await expect(page.getByText(/couldn.t load fund data/i)).toBeVisible();
  await page.getByRole("button", { name: /retry fund loading/i }).click();
  await expect(page.getByText("Load an example portfolio")).toBeVisible({ timeout: 30_000 });
  expect(attempts).toBe(2);
});

test("retries shared-run loading instead of starting a new simulation", async ({ page }) => {
  let attempts = 0;
  await page.route("**/api/simulate/missing-run", async (route) => {
    attempts += 1;
    await route.fulfill({
      status: 404,
      contentType: "application/json",
      body: JSON.stringify({ detail: "not found", code: "RUN_NOT_FOUND" }),
    });
  });

  await page.goto("/?run=missing-run");
  await expect(page.getByText(/couldn.t load shared run/i)).toBeVisible();
  await page.getByRole("button", { name: /retry shared run loading/i }).click();
  await expect(page.getByText(/couldn.t load shared run/i)).toBeVisible();
  expect(attempts).toBe(2);
});
