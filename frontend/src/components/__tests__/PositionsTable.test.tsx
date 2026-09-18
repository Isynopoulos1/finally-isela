import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { PositionsTable } from "../PositionsTable";
import type { Position } from "@/lib/types";

describe("PositionsTable P&L display", () => {
  it("shows a profitable position in green with formatted values", () => {
    const positions: Position[] = [
      {
        ticker: "AAPL",
        quantity: 10,
        avg_cost: 150,
        current_price: 190,
        unrealized_pnl: 400,
        unrealized_pnl_pct: 26.67,
      },
    ];

    render(<PositionsTable positions={positions} />);

    expect(screen.getByText("AAPL")).toBeInTheDocument();
    const pnlCell = screen.getByTestId("pnl-AAPL");
    expect(pnlCell).toHaveTextContent("$400.00");
    expect(pnlCell.className).toContain("text-up");
  });

  it("shows a losing position in red", () => {
    const positions: Position[] = [
      {
        ticker: "TSLA",
        quantity: 5,
        avg_cost: 300,
        current_price: 250,
        unrealized_pnl: -250,
        unrealized_pnl_pct: -16.67,
      },
    ];

    render(<PositionsTable positions={positions} />);

    const pnlCell = screen.getByTestId("pnl-TSLA");
    expect(pnlCell).toHaveTextContent("-$250.00");
    expect(pnlCell.className).toContain("text-down");
  });

  it("shows an empty state with no positions", () => {
    render(<PositionsTable positions={[]} />);
    expect(screen.getByText("No open positions")).toBeInTheDocument();
  });
});
