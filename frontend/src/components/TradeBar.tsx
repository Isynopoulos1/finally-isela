"use client";

import { useState } from "react";
import type { TradeSide } from "@/lib/types";

interface TradeBarProps {
  onTrade: (ticker: string, quantity: number, side: TradeSide) => Promise<void>;
}

export function TradeBar({ onTrade }: TradeBarProps) {
  const [ticker, setTicker] = useState("");
  const [quantity, setQuantity] = useState("");
  const [pending, setPending] = useState<TradeSide | null>(null);
  const [error, setError] = useState<string | null>(null);

  const submit = async (side: TradeSide) => {
    const qty = Number(quantity);
    const symbol = ticker.trim().toUpperCase();
    if (!symbol || !Number.isFinite(qty) || qty <= 0) {
      setError("Enter a ticker and a positive quantity");
      return;
    }
    setPending(side);
    setError(null);
    try {
      await onTrade(symbol, qty, side);
      setQuantity("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Trade failed");
    } finally {
      setPending(null);
    }
  };

  return (
    <div className="flex flex-wrap items-center gap-2">
      <input
        value={ticker}
        onChange={(event) => setTicker(event.target.value)}
        placeholder="Ticker"
        aria-label="Trade ticker"
        className="w-24 border border-border bg-bg px-2 py-1.5 font-mono text-sm text-text placeholder:text-text-muted focus:border-blue focus:outline-none"
      />
      <input
        value={quantity}
        onChange={(event) => setQuantity(event.target.value)}
        placeholder="Quantity"
        aria-label="Trade quantity"
        inputMode="decimal"
        className="w-28 border border-border bg-bg px-2 py-1.5 font-mono text-sm text-text placeholder:text-text-muted focus:border-blue focus:outline-none"
      />
      <button
        type="button"
        disabled={pending !== null}
        onClick={() => submit("buy")}
        className="bg-purple px-4 py-1.5 text-sm font-medium text-text hover:brightness-110 disabled:opacity-50"
      >
        Buy
      </button>
      <button
        type="button"
        disabled={pending !== null}
        onClick={() => submit("sell")}
        className="border border-border px-4 py-1.5 text-sm font-medium text-text hover:border-down hover:text-down disabled:opacity-50"
      >
        Sell
      </button>
      {error && <span className="text-xs text-down">{error}</span>}
    </div>
  );
}
