"use client";

import { useEffect, useRef, useState } from "react";
import { formatCurrency, formatPercent } from "@/lib/format";
import { PriceChart, type PricePoint } from "./PriceChart";
import type { PriceTick } from "@/lib/types";

interface WatchlistRowProps {
  ticker: string;
  price: number | null;
  ticks: PriceTick[];
  selected: boolean;
  onSelect: (ticker: string) => void;
  onRemove: (ticker: string) => void;
}

export function WatchlistRow({
  ticker,
  price,
  ticks,
  selected,
  onSelect,
  onRemove,
}: WatchlistRowProps) {
  const [flash, setFlash] = useState<"up" | "down" | null>(null);
  const lastPriceRef = useRef<number | null>(price);

  useEffect(() => {
    if (price === null) return;
    if (lastPriceRef.current !== null && price !== lastPriceRef.current) {
      setFlash(price > lastPriceRef.current ? "up" : "down");
    }
    lastPriceRef.current = price;
  }, [price]);

  useEffect(() => {
    if (!flash) return;
    const timeout = setTimeout(() => setFlash(null), 500);
    return () => clearTimeout(timeout);
  }, [flash]);

  const points: PricePoint[] = ticks.map((tick) => ({ time: tick.timestamp, value: tick.price }));
  const first = points[0]?.value;
  const changePercent = first && price !== null ? ((price - first) / first) * 100 : null;

  return (
    <div
      role="button"
      tabIndex={0}
      data-testid={`watchlist-row-${ticker}`}
      onClick={() => onSelect(ticker)}
      onKeyDown={(event) => {
        if (event.key === "Enter") onSelect(ticker);
      }}
      className={`grid cursor-pointer grid-cols-[1fr_auto_auto_64px_20px] items-center gap-2 border-b border-border px-3 py-2 text-sm transition-colors hover:bg-panel-raised ${
        selected ? "bg-panel-raised" : ""
      } ${flash === "up" ? "flash-up" : ""} ${flash === "down" ? "flash-down" : ""}`}
    >
      <span className="truncate font-mono font-medium text-text">{ticker}</span>
      <span className="font-mono tabular-nums text-text">
        {price !== null ? formatCurrency(price) : "—"}
      </span>
      <span
        className={`font-mono text-xs tabular-nums ${
          changePercent === null ? "text-text-muted" : changePercent >= 0 ? "text-up" : "text-down"
        }`}
      >
        {changePercent === null ? "—" : formatPercent(changePercent)}
      </span>
      <span className="h-8 w-16">
        <PriceChart
          id={ticker}
          data={points}
          variant="compact"
          color={changePercent !== null && changePercent < 0 ? "#f2545b" : "#3ecf8e"}
        />
      </span>
      <button
        type="button"
        onClick={(event) => {
          event.stopPropagation();
          onRemove(ticker);
        }}
        aria-label={`Remove ${ticker} from watchlist`}
        className="text-text-muted hover:text-down"
      >
        ×
      </button>
    </div>
  );
}
