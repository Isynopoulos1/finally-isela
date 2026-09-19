"use client";

import { PriceChart, type PricePoint } from "./PriceChart";
import { formatCurrency } from "@/lib/format";
import type { PriceTick } from "@/lib/types";

interface MainChartProps {
  ticker: string | null;
  ticks: PriceTick[];
}

export function MainChart({ ticker, ticks }: MainChartProps) {
  const points: PricePoint[] = ticks.map((tick) => ({ time: tick.timestamp, value: tick.price }));
  const latest = points.at(-1)?.value;

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-baseline justify-between px-1 pb-2">
        <span className="font-mono text-base font-semibold text-text">
          {ticker ?? "Select a ticker"}
        </span>
        {latest !== undefined && (
          <span className="font-mono text-sm tabular-nums text-text-muted">
            {formatCurrency(latest)}
          </span>
        )}
      </div>
      <div className="min-h-0 flex-1">
        {ticker ? (
          <PriceChart id={ticker} data={points} variant="full" color="#209dd7" />
        ) : (
          <div className="flex h-full items-center justify-center text-sm text-text-muted">
            Click a ticker in the watchlist to see its chart
          </div>
        )}
      </div>
    </div>
  );
}
