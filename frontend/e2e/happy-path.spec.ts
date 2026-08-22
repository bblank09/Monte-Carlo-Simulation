import { test, expect } from "@playwright/test";

// The real SEC Open Data API backing /api/funds and /api/simulate is slow
// and occasionally flaky (cold cache, third-party rate limiting) -- this
// test's own timeout is bumped well past the individual step timeouts below
// to leave real margin, matching the project's disclosed constraint (see
// playwright.config.ts and CLAUDE.md's "Landmines" section).
test.setTimeout(180_000);

test("build a portfolio, run a historical simulation, and see results", async ({ page, browser }) => {
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

  const continueToParams = page.getByRole("button", { name: /continue to assumptions/i });
  await expect(continueToParams).toBeEnabled({ timeout: 30_000 });
  await continueToParams.click();

  // Parameters step
  await expect(page.getByText("Set your simulation assumptions")).toBeVisible();
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
  await expect(page.getByText(/ended with a positive balance|funded the configured cashflows/i)).toBeVisible({ timeout: 120_000 });
  await expect(page.getByRole("tab", { name: "Growth" })).toBeVisible();
  await expect(page).toHaveURL(/[?&]run=run_\d{8}_\d{6}_[0-9a-f]{8}/);
  await expect(page.getByRole("button", { name: "Result JSON" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Copy shareable link" })).toBeVisible();

  // Results tabs. Each tab should render its decision-oriented section without a
  // runtime error, while keeping the same tab set as the Backtest shell.
  const tabChecks = [
    ["Overview", /Decision summary/],
    ["Growth", /Projected value milestones/],
    ["Distribution", /Probability of Ending Below Target/],
    ["Metrics", /Performance outcomes/],
    ["Risk & Correlation", /Loss probability/],
    ["Report", /Simulation diagnostics/],
  ] as const;
  for (const [tab, heading] of tabChecks) {
    const tabButton = page.getByRole("tab", { name: tab, exact: true });
    await tabButton.click();
    await expect(tabButton).toHaveAttribute("aria-selected", "true");
    await expect(page.getByRole("heading", { name: heading })).toBeVisible();
    if (tab === "Distribution") {
      await expect(page.getByLabel("Target ending balance")).toBeVisible();
      await expect(page.getByText(/of paths end at or below target/i)).toBeVisible();
    }
  }

  const sharedUrl = page.url();
  const visitorContext = await browser.newContext();
  const visitorPage = await visitorContext.newPage();
  try {
    await visitorPage.goto(sharedUrl);
    await expect(visitorPage.getByRole("heading", { name: /Historical model · 30-year horizon/ })).toBeVisible({ timeout: 30_000 });
    await expect(visitorPage.getByRole("button", { name: "Result JSON" })).toBeVisible();
  } finally {
    await visitorContext.close();
  }
});
