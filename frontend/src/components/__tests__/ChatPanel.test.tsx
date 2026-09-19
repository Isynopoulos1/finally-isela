import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { ChatPanel } from "../ChatPanel";
import type { ChatMessage } from "@/lib/types";

describe("ChatPanel", () => {
  it("renders conversation history and inline executed actions", () => {
    const messages: ChatMessage[] = [
      { id: "1", role: "user", content: "Buy 10 AAPL" },
      {
        id: "2",
        role: "assistant",
        content: "Done, bought 10 shares of AAPL.",
        actions: { trades: [{ ticker: "AAPL", side: "buy", quantity: 10 }] },
      },
    ];

    render(
      <ChatPanel messages={messages} loading={false} onSend={vi.fn()} open onToggle={() => {}} />,
    );

    expect(screen.getByText("Buy 10 AAPL")).toBeInTheDocument();
    expect(screen.getByText("Done, bought 10 shares of AAPL.")).toBeInTheDocument();
    expect(screen.getByText("Executed: buy 10 AAPL")).toBeInTheDocument();
  });

  it("shows a loading indicator while awaiting a response", () => {
    render(<ChatPanel messages={[]} loading onSend={vi.fn()} open onToggle={() => {}} />);
    expect(screen.getByRole("status")).toHaveTextContent("FinAlly is thinking");
  });

  it("sends the trimmed message and clears the input", async () => {
    const user = userEvent.setup();
    const onSend = vi.fn().mockResolvedValue(undefined);

    render(<ChatPanel messages={[]} loading={false} onSend={onSend} open onToggle={() => {}} />);

    const input = screen.getByLabelText("Chat message");
    await user.type(input, "  What's my P&L?  ");
    await user.click(screen.getByRole("button", { name: "Send" }));

    expect(onSend).toHaveBeenCalledWith("What's my P&L?");
    expect(input).toHaveValue("");
  });

  it("collapses to a toggle button when closed", () => {
    render(<ChatPanel messages={[]} loading={false} onSend={vi.fn()} open={false} onToggle={() => {}} />);
    expect(screen.getByRole("button", { name: "Open AI chat" })).toBeInTheDocument();
  });
});
