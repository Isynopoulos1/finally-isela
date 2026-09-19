import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { WatchlistRow } from "../WatchlistRow";

vi.mock("../PriceChart", () => ({
  PriceChart: () => <div data-testid="chart-stub" />,
}));

describe("WatchlistRow price flash", () => {
  it("flashes green when price ticks up", () => {
    const { rerender } = render(
      <WatchlistRow
        ticker="AAPL"
        price={100}
        ticks={[]}
        selected={false}
        onSelect={() => {}}
        onRemove={() => {}}
      />,
    );

    const row = screen.getByTestId("watchlist-row-AAPL");
    expect(row.className).not.toContain("flash-up");

    rerender(
      <WatchlistRow
        ticker="AAPL"
        price={101}
        ticks={[]}
        selected={false}
        onSelect={() => {}}
        onRemove={() => {}}
      />,
    );

    expect(screen.getByTestId("watchlist-row-AAPL").className).toContain("flash-up");
  });

  it("flashes red when price ticks down", () => {
    const { rerender } = render(
      <WatchlistRow
        ticker="MSFT"
        price={100}
        ticks={[]}
        selected={false}
        onSelect={() => {}}
        onRemove={() => {}}
      />,
    );

    rerender(
      <WatchlistRow
        ticker="MSFT"
        price={99}
        ticks={[]}
        selected={false}
        onSelect={() => {}}
        onRemove={() => {}}
      />,
    );

    expect(screen.getByTestId("watchlist-row-MSFT").className).toContain("flash-down");
  });

  it("does not flash when price is unchanged", () => {
    const { rerender } = render(
      <WatchlistRow
        ticker="GOOGL"
        price={100}
        ticks={[]}
        selected={false}
        onSelect={() => {}}
        onRemove={() => {}}
      />,
    );

    rerender(
      <WatchlistRow
        ticker="GOOGL"
        price={100}
        ticks={[]}
        selected={false}
        onSelect={() => {}}
        onRemove={() => {}}
      />,
    );

    const row = screen.getByTestId("watchlist-row-GOOGL");
    expect(row.className).not.toContain("flash-up");
    expect(row.className).not.toContain("flash-down");
  });
});
