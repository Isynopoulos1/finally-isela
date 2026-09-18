"use client";

import { useState, type FormEvent } from "react";
import { WatchlistRow } from "./WatchlistRow";
import type { PriceTick, WatchlistItem } from "@/lib/types";

interface WatchlistProps {
  items: WatchlistItem[];
  priceHistory: Record<string, PriceTick[]>;
  selectedTicker: string | null;
  onSelect: (ticker: string) => void;
  onAdd: (ticker: string) => Promise<void>;
  onRemove: (ticker: string) => Promise<void>;
}

export function Watchlist({
  items,
  priceHistory,
  selectedTicker,
  onSelect,
  onAdd,
  onRemove,
}: WatchlistProps) {
  const [draft, setDraft] = useState("");
  const [error, setError] = useState<string | null>(null);

  const handleAdd = async (event: FormEvent) => {
    event.preventDefault();
    const ticker = draft.trim().toUpperCase();
    if (!ticker) return;
    try {
      await onAdd(ticker);
      setDraft("");
      setError(null);
    } catch {
      setError(`Couldn't add ${ticker}`);
    }
  };

  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-border px-3 py-2 text-sm font-medium text-text">
        Watchlist
      </div>
      <form onSubmit={handleAdd} className="flex gap-1 border-b border-border p-2">
        <input
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          placeholder="Add ticker"
          aria-label="Add ticker"
          className="min-w-0 flex-1 border border-border bg-bg px-2 py-1 font-mono text-xs text-text placeholder:text-text-muted focus:border-blue focus:outline-none"
        />
        <button
          type="submit"
          className="bg-blue px-2 py-1 text-xs font-medium text-bg hover:brightness-110"
        >
          Add
        </button>
      </form>
      {error && <p className="px-3 py-1 text-xs text-down">{error}</p>}
      <div className="flex-1 overflow-y-auto">
        {items.map((item) => (
          <WatchlistRow
            key={item.ticker}
            ticker={item.ticker}
            price={priceHistory[item.ticker]?.at(-1)?.price ?? item.price}
            ticks={priceHistory[item.ticker] ?? []}
            selected={item.ticker === selectedTicker}
            onSelect={onSelect}
            onRemove={onRemove}
          />
        ))}
      </div>
    </div>
  );
}
