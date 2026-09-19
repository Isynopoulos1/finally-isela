import { test, expect, type Page } from "@playwright/test";

const DEFAULT_TICKERS = [
  "AAPL",
  "GOOGL",
  "MSFT",
  "AMZN",
  "TSLA",
  "NVDA",
  "META",
  "JPM",
  "V",
  "NFLX",
];

// All scenarios share one backend/db instance (single-user app, no auth — see
// planning/DECISIONS.md #6), so tests run serially, in a deliberate order, in
// one worker (see playwright.config.ts). Each test's state is a precondition
// for the next.
test.describe.configure({ mode: "serial" });

async function waitForLivePrice(page: Page, ticker: string) {
  const row = page.getByTestId(`watchlist-row-${ticker}`);
  await expect(row).toBeVisible();
  await expect(row.locator("span").nth(1)).not.toHaveText("—", { timeout: 10_000 });
}

test.describe("FinAlly E2E", () => {
  test("fresh start: default watchlist, $10k cash, live prices", async ({ page }) => {
    await page.goto("/");

    for (const ticker of DEFAULT_TICKERS) {
      await expect(page.getByTestId(`watchlist-row-${ticker}`)).toBeVisible();
    }

    await expect(page.getByTestId("cash-balance")).toHaveText("$10,000.00");
    await expect(page.getByTestId("portfolio-total-value")).toHaveText("$10,000.00");

    // SSE is streaming: at least one row should get a live (non-placeholder) price.
    await waitForLivePrice(page, "AAPL");

    await expect(page.getByTestId("connection-status")).toHaveAttribute("aria-label", "Live");
  });

  test("add and remove a ticker from the watchlist", async ({ page }) => {
    await page.goto("/");

    await page.getByLabel("Add ticker").fill("DIS");
    await page.getByRole("button", { name: "Add" }).click();
    await expect(page.getByTestId("watchlist-row-DIS")).toBeVisible();

    await page.getByLabel("Remove DIS from watchlist").click();
    await expect(page.getByTestId("watchlist-row-DIS")).toHaveCount(0);
  });

  test("buy shares: cash decreases, position appears, total updates", async ({ page }) => {
    await page.goto("/");

    const cashBefore = await page.getByTestId("cash-balance").textContent();

    await page.getByLabel("Trade ticker").fill("AAPL");
    await page.getByLabel("Trade quantity").fill("2");
    await page.getByRole("button", { name: "Buy" }).click();

    await expect(page.getByTestId("positions-table")).toContainText("AAPL");
    await expect
      .poll(async () => page.getByTestId("cash-balance").textContent())
      .not.toBe(cashBefore);

    const cashText = await page.getByTestId("cash-balance").textContent();
    const cashValue = Number(cashText!.replace(/[^0-9.-]/g, ""));
    expect(cashValue).toBeLessThan(10000);
  });

  test("sell shares: cash increases, position disappears", async ({ page }) => {
    await page.goto("/");

    await expect(page.getByTestId("positions-table")).toContainText("AAPL");
    const cashBefore = await page.getByTestId("cash-balance").textContent();

    await page.getByLabel("Trade ticker").fill("AAPL");
    await page.getByLabel("Trade quantity").fill("2");
    await page.getByRole("button", { name: "Sell" }).click();

    await expect
      .poll(async () => page.getByTestId("cash-balance").textContent())
      .not.toBe(cashBefore);

    const cashText = await page.getByTestId("cash-balance").textContent();
    const cashValue = Number(cashText!.replace(/[^0-9.-]/g, ""));
    expect(cashValue).toBeGreaterThan(9990); // back near $10k, minus simulator price drift

    await expect(page.getByTestId("positions-table")).toContainText("No open positions");
  });

  test("portfolio visualization: heatmap and P&L chart render after a buy", async ({ page }) => {
    await page.goto("/");

    await page.getByLabel("Trade ticker").fill("MSFT");
    await page.getByLabel("Trade quantity").fill("1");
    await page.getByRole("button", { name: "Buy" }).click();

    await expect(page.getByTestId("heatmap-rect-MSFT")).toBeVisible();

    // portfolio_snapshots gets a row on every trade (DECISIONS.md #7), so after
    // the trades in this run there are >1 points and the chart (not the empty
    // state) should render.
    await expect(page.getByTestId("pnl-chart-empty")).toHaveCount(0);
    await expect(page.getByTestId("pnl-chart").locator("canvas").first()).toBeVisible();
  });

  test("AI chat: 'buy 5 AAPL' executes a trade end to end", async ({ page, request }) => {
    await page.goto("/");

    await page.getByLabel("Chat message").fill("buy 5 AAPL");
    await page.getByRole("button", { name: "Send" }).click();

    const assistantMessage = page.getByTestId("chat-message-assistant").last();
    await expect(assistantMessage).toContainText("Mock: buying 5 AAPL", { timeout: 10_000 });
    await expect(assistantMessage).toContainText("Executed: buy 5 AAPL");

    const portfolio = await (await request.get("/api/portfolio")).json();
    const aapl = portfolio.positions.find((p: { ticker: string }) => p.ticker === "AAPL");
    expect(aapl).toBeTruthy();
    expect(aapl.quantity).toBe(5);
  });

  test("AI chat: 'add PYPL to watchlist' updates the watchlist UI", async ({ page }) => {
    await page.goto("/");

    await page.getByLabel("Chat message").fill("add PYPL to watchlist");
    await page.getByRole("button", { name: "Send" }).click();

    const assistantMessage = page.getByTestId("chat-message-assistant").last();
    await expect(assistantMessage).toContainText("Mock: adding PYPL", { timeout: 10_000 });

    await expect(page.getByTestId("watchlist-row-PYPL")).toBeVisible();
  });

  test("SSE connection indicator shows connected during normal operation", async ({ page }) => {
    // True disconnect/reconnect (killing the server mid-stream) isn't simulated
    // here: the backend is shared by the whole suite, and killing it would
    // break every other serial test in this file. This only verifies the
    // steady-state "connected" indication EventSource.onopen drives.
    await page.goto("/");
    const status = page.getByTestId("connection-status");
    await expect(status).toHaveAttribute("aria-label", "Live");
    await page.waitForTimeout(2000);
    await expect(status).toHaveAttribute("aria-label", "Live");
  });
});
