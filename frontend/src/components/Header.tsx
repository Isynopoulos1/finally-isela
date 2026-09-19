"use client";

import { formatCurrency } from "@/lib/format";
import type { ConnectionStatus } from "@/lib/usePriceStream";

interface HeaderProps {
  totalValue: number;
  cashBalance: number;
  status: ConnectionStatus;
}

const STATUS_LABEL: Record<ConnectionStatus, string> = {
  connected: "Live",
  reconnecting: "Reconnecting",
  disconnected: "Disconnected",
};

const STATUS_COLOR: Record<ConnectionStatus, string> = {
  connected: "bg-up",
  reconnecting: "bg-yellow",
  disconnected: "bg-down",
};

export function Header({ totalValue, cashBalance, status }: HeaderProps) {
  return (
    <header className="flex h-14 shrink-0 items-center justify-between border-b border-border bg-panel px-4">
      <div className="flex items-baseline gap-2">
        <span className="text-lg font-semibold tracking-tight text-text">FinAlly</span>
        <span className="text-xs text-text-muted">the finance ally</span>
      </div>
      <div className="flex items-center gap-6">
        <div className="text-right">
          <div className="text-xs text-text-muted">Portfolio value</div>
          <div
            data-testid="portfolio-total-value"
            className="font-mono text-lg font-semibold tabular-nums text-text"
          >
            {formatCurrency(totalValue)}
          </div>
        </div>
        <div className="text-right">
          <div className="text-xs text-text-muted">Cash</div>
          <div data-testid="cash-balance" className="font-mono text-lg tabular-nums text-text-muted">
            {formatCurrency(cashBalance)}
          </div>
        </div>
        <div
          className="flex items-center gap-2"
          role="status"
          data-testid="connection-status"
          aria-label={STATUS_LABEL[status]}
        >
          <span className={`h-2.5 w-2.5 rounded-full ${STATUS_COLOR[status]}`} />
          <span className="text-xs text-text-muted">{STATUS_LABEL[status]}</span>
        </div>
      </div>
    </header>
  );
}
