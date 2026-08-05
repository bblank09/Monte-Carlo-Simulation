import { test, expect } from "@playwright/test";

// The real SEC Open Data API backing /api/funds and /api/simulate is slow
// and occasionally flaky (cold cache, third-party rate limiting) -- this
// test's own timeout is bumped well past the individual step timeouts below
// to leave real margin, matching the project's disclosed constraint (see
// playwright.config.ts and CLAUDE.md's "Landmines" section).
test.setTimeout(180_000);

test("build a portfolio, run a historical simulation, and see results", async ({ page }) => {
  await page.goto("/");

  // Portfolio step. "Load an example portfolio" depends on /api/funds having
  // resolved first (see PortfolioStep.loadExample, which no-ops until at
  // least two funds are loaded) -- retry the click until the rows are
  // actually populated instead of assuming one click suffices.
  const weightHeader = page.getByText("Weight %");
  await expect(async () => {
    await page.getByText("Load an example portfolio").click();
    await expect(weightHeader).toBeVisible();
    await expect(page.getByText("100%", { exact: true })).toBeVisible();
  }).toPass({ timeout: 60_000 });

  const continueToParams = page.getByRole("button", { name: /continue to parameters/i });
  await expect(continueToParams).toBeEnabled({ timeout: 30_000 });
  await continueToParams.click();

  // Parameters step
  await expect(page.getByText("Set your simulation parameters")).toBeVisible();
  const continueToResults = page.getByRole("button", { name: /continue to results/i });
  await expect(continueToResults).toBeVisible();
  // Guard against the step-transition fade animation making the click land
  // before layout has settled -- confirm the button's position is stable,
  // then click, then verify the "Running..." state actually engaged rather
  // than trusting that the click was received.
  await continueToResults.scrollIntoViewIfNeeded();
  await continueToResults.click();
  await expect(page.getByRole("button", { name: /running/i })).toBeVisible({ timeout: 15_000 });

  // Results step
  await expect(page.getByText(/survived all withdrawals/i)).toBeVisible({ timeout: 120_000 });
  await expect(page.getByRole("button", { name: "Growth" })).toBeVisible();
});
