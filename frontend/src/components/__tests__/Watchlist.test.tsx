import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { Watchlist } from "../Watchlist";

vi.mock("../PriceChart", () => ({
  PriceChart: () => <div data-testid="chart-stub" />,
}));

describe("Watchlist add/remove", () => {
  it("submits a trimmed, uppercased ticker and clears the input", async () => {
    const user = userEvent.setup();
    const onAdd = vi.fn().mockResolvedValue(undefined);

    render(
      <Watchlist
        items={[]}
        priceHistory={{}}
        selectedTicker={null}
        onSelect={() => {}}
        onAdd={onAdd}
        onRemove={vi.fn()}
      />,
    );

    const input = screen.getByLabelText("Add ticker");
    await user.type(input, "  pypl ");
    await user.click(screen.getByRole("button", { name: "Add" }));

    expect(onAdd).toHaveBeenCalledWith("PYPL");
  });

  it("calls onRemove for the clicked ticker without selecting it", async () => {
    const user = userEvent.setup();
    const onRemove = vi.fn().mockResolvedValue(undefined);
    const onSelect = vi.fn();

    render(
      <Watchlist
        items={[{ ticker: "AAPL", price: 190 }]}
        priceHistory={{}}
        selectedTicker={null}
        onSelect={onSelect}
        onAdd={vi.fn()}
        onRemove={onRemove}
      />,
    );

    await user.click(screen.getByRole("button", { name: "Remove AAPL from watchlist" }));

    expect(onRemove).toHaveBeenCalledWith("AAPL");
    expect(onSelect).not.toHaveBeenCalled();
  });
});
