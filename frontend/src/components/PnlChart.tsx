"use client";

import { PriceChart, type PricePoint } from "./PriceChart";
import type { PortfolioSnapshot } from "@/lib/types";

interface PnlChartProps {
  snapshots: PortfolioSnapshot[];
}

export function PnlChart({ snapshots }: PnlChartProps) {
  const points: PricePoint[] = snapshots.map((snapshot) => ({
    time: snapshot.recorded_at,
    value: snapshot.total_value,
  }));

  return (
    <div className="flex h-full flex-col">
      <div className="px-1 pb-2 text-sm font-medium text-text">Portfolio value</div>
      <div data-testid="pnl-chart" className="min-h-0 flex-1">
        {points.length > 1 ? (
          <PriceChart id="portfolio" data={points} variant="full" color="#ecad0a" />
        ) : (
          <div data-testid="pnl-chart-empty" className="flex h-full items-center justify-center text-sm text-text-muted">
            Not enough history yet
          </div>
        )}
      </div>
    </div>
  );
}
