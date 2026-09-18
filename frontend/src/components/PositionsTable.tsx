"use client";

import { formatCurrency, formatNumber, formatPercent } from "@/lib/format";
import type { Position } from "@/lib/types";

interface PositionsTableProps {
  positions: Position[];
}

export function PositionsTable({ positions }: PositionsTableProps) {
  return (
    <div className="overflow-x-auto">
      <table data-testid="positions-table" className="w-full border-collapse text-sm">
        <thead>
          <tr className="border-b border-border text-left whitespace-nowrap text-text-muted">
            <th className="py-2 pr-4 font-normal">Ticker</th>
            <th className="py-2 pr-4 text-right font-normal">Qty</th>
            <th className="py-2 pr-4 text-right font-normal">Avg cost</th>
            <th className="py-2 pr-4 text-right font-normal">Price</th>
            <th className="py-2 pr-4 text-right font-normal">Unrealized P&amp;L</th>
            <th className="py-2 text-right font-normal">Change</th>
          </tr>
        </thead>
        <tbody>
          {positions.length === 0 && (
            <tr>
              <td colSpan={6} className="py-4 text-center text-text-muted">
                No open positions
              </td>
            </tr>
          )}
          {positions.map((position) => (
            <tr key={position.ticker} className="border-b border-border font-mono">
              <td className="py-2 pr-4 font-medium text-text">{position.ticker}</td>
              <td className="py-2 pr-4 text-right tabular-nums text-text">
                {formatNumber(position.quantity)}
              </td>
              <td className="py-2 pr-4 text-right tabular-nums text-text-muted">
                {formatCurrency(position.avg_cost)}
              </td>
              <td className="py-2 pr-4 text-right tabular-nums text-text">
                {formatCurrency(position.current_price)}
              </td>
              <td
                data-testid={`pnl-${position.ticker}`}
                className={`py-2 pr-4 text-right tabular-nums ${
                  position.unrealized_pnl >= 0 ? "text-up" : "text-down"
                }`}
              >
                {formatCurrency(position.unrealized_pnl)}
              </td>
              <td
                className={`py-2 text-right tabular-nums ${
                  position.unrealized_pnl_pct >= 0 ? "text-up" : "text-down"
                }`}
              >
                {formatPercent(position.unrealized_pnl_pct)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
