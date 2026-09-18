"use client";

import { useEffect, useRef, useState } from "react";
import { squarify } from "@/lib/treemap";
import { formatPercent } from "@/lib/format";
import type { Position } from "@/lib/types";

interface PortfolioHeatmapProps {
  positions: Position[];
}

function pnlColor(percentChange: number): string {
  const clamped = Math.max(-15, Math.min(15, percentChange));
  const intensity = 20 + (Math.abs(clamped) / 15) * 60;
  const base = percentChange >= 0 ? "var(--color-up)" : "var(--color-down)";
  return `color-mix(in srgb, ${base} ${intensity}%, var(--color-panel))`;
}

export function PortfolioHeatmap({ positions }: PortfolioHeatmapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [size, setSize] = useState({ width: 0, height: 0 });

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    const observer = new ResizeObserver((entries) => {
      const { width, height } = entries[0].contentRect;
      setSize({ width, height });
    });
    observer.observe(container);
    return () => observer.disconnect();
  }, []);

  const totalValue = positions.reduce((sum, p) => sum + p.quantity * p.current_price, 0);
  const rects = squarify(
    positions.map((p) => ({ id: p.ticker, value: Math.max(p.quantity * p.current_price, 0.01) })),
    size.width,
    size.height,
  );

  return (
    <div ref={containerRef} className="relative h-full w-full">
      {positions.length === 0 && (
        <p className="p-3 text-sm text-text-muted">No open positions yet.</p>
      )}
      {rects.map((rect) => {
        const position = positions.find((p) => p.ticker === rect.id);
        if (!position) return null;
        const weight =
          totalValue > 0 ? ((position.quantity * position.current_price) / totalValue) * 100 : 0;
        return (
          <div
            key={rect.id}
            data-testid={`heatmap-rect-${rect.id}`}
            className="absolute flex flex-col justify-between overflow-hidden border border-border p-2"
            style={{
              left: rect.x,
              top: rect.y,
              width: rect.width,
              height: rect.height,
              backgroundColor: pnlColor(position.unrealized_pnl_pct),
            }}
          >
            <span className="font-mono text-sm font-semibold text-text">{position.ticker}</span>
            <div className="font-mono text-xs text-text">
              <div>{weight.toFixed(1)}%</div>
              <div>{formatPercent(position.unrealized_pnl_pct)}</div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
