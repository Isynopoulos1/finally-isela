"use client";

import { useCallback, useEffect, useState } from "react";
import { ChatPanel } from "@/components/ChatPanel";
import { Header } from "@/components/Header";
import { MainChart } from "@/components/MainChart";
import { PnlChart } from "@/components/PnlChart";
import { PortfolioHeatmap } from "@/components/PortfolioHeatmap";
import { PositionsTable } from "@/components/PositionsTable";
import { TradeBar } from "@/components/TradeBar";
import { Watchlist } from "@/components/Watchlist";
import { api } from "@/lib/api";
import type { ChatMessage, Portfolio, PortfolioSnapshot, TradeSide, WatchlistItem } from "@/lib/types";
import { usePriceStream } from "@/lib/usePriceStream";

const PORTFOLIO_POLL_MS = 4000;
const HISTORY_POLL_MS = 10000;

const EMPTY_PORTFOLIO: Portfolio = { cash_balance: 10000, positions: [], total_value: 10000 };

export default function Home() {
  const { history, status } = usePriceStream();
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([]);
  const [portfolio, setPortfolio] = useState<Portfolio>(EMPTY_PORTFOLIO);
  const [snapshots, setSnapshots] = useState<PortfolioSnapshot[]>([]);
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [chatLoading, setChatLoading] = useState(false);
  const [chatOpen, setChatOpen] = useState(true);

  const refreshWatchlist = useCallback(async () => {
    const items = await api.getWatchlist();
    setWatchlist(items);
    setSelectedTicker((current) => current ?? items[0]?.ticker ?? null);
  }, []);

  const refreshPortfolio = useCallback(async () => {
    setPortfolio(await api.getPortfolio());
  }, []);

  const refreshHistory = useCallback(async () => {
    setSnapshots(await api.getHistory());
  }, []);

  useEffect(() => {
    let ignore = false;
    async function load() {
      await Promise.all([
        refreshWatchlist().catch(() => {}),
        refreshPortfolio().catch(() => {}),
        refreshHistory().catch(() => {}),
      ]);
    }
    if (!ignore) load();
    return () => {
      ignore = true;
    };
  }, [refreshWatchlist, refreshPortfolio, refreshHistory]);

  useEffect(() => {
    let ignore = false;
    const portfolioTimer = setInterval(() => {
      if (!ignore) refreshPortfolio().catch(() => {});
    }, PORTFOLIO_POLL_MS);
    const historyTimer = setInterval(() => {
      if (!ignore) refreshHistory().catch(() => {});
    }, HISTORY_POLL_MS);
    return () => {
      ignore = true;
      clearInterval(portfolioTimer);
      clearInterval(historyTimer);
    };
  }, [refreshPortfolio, refreshHistory]);

  const handleAddTicker = async (ticker: string) => {
    await api.addTicker(ticker);
    await refreshWatchlist();
  };

  const handleRemoveTicker = async (ticker: string) => {
    await api.removeTicker(ticker);
    await refreshWatchlist();
    setSelectedTicker((current) => (current === ticker ? null : current));
  };

  const handleTrade = async (ticker: string, quantity: number, side: TradeSide) => {
    await api.trade(ticker, quantity, side);
    await Promise.all([refreshPortfolio(), refreshHistory()]);
  };

  const handleSendChat = async (text: string) => {
    const userMessage: ChatMessage = { id: crypto.randomUUID(), role: "user", content: text };
    setMessages((prev) => [...prev, userMessage]);
    setChatLoading(true);
    try {
      const response = await api.sendChatMessage(text);
      const assistantMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: response.message,
        actions: { trades: response.trades, watchlist_changes: response.watchlist_changes },
      };
      setMessages((prev) => [...prev, assistantMessage]);
      if (response.trades?.length || response.watchlist_changes?.length) {
        await Promise.all([refreshPortfolio(), refreshHistory(), refreshWatchlist()]);
      }
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: "Something went wrong reaching FinAlly. Try again.",
        },
      ]);
    } finally {
      setChatLoading(false);
    }
  };

  const selectedTicks = selectedTicker ? (history[selectedTicker] ?? []) : [];

  return (
    <div className="flex h-dvh flex-col bg-bg text-text">
      <Header totalValue={portfolio.total_value} cashBalance={portfolio.cash_balance} status={status} />
      <div className="flex flex-1 overflow-hidden">
        <aside className="w-72 shrink-0 overflow-hidden border-r border-border">
          <Watchlist
            items={watchlist}
            priceHistory={history}
            selectedTicker={selectedTicker}
            onSelect={setSelectedTicker}
            onAdd={handleAddTicker}
            onRemove={handleRemoveTicker}
          />
        </aside>
        <main className="flex flex-1 flex-col overflow-y-auto">
          <section className="h-72 shrink-0 border-b border-border p-3">
            <MainChart ticker={selectedTicker} ticks={selectedTicks} />
          </section>
          <section className="shrink-0 border-b border-border p-3">
            <TradeBar onTrade={handleTrade} />
          </section>
          <section className="grid shrink-0 grid-cols-2 border-b border-border">
            <div className="h-56 border-r border-border p-3">
              <PortfolioHeatmap positions={portfolio.positions} />
            </div>
            <div className="h-56 p-3">
              <PnlChart snapshots={snapshots} />
            </div>
          </section>
          <section className="p-3">
            <PositionsTable positions={portfolio.positions} />
          </section>
        </main>
        <ChatPanel
          messages={messages}
          loading={chatLoading}
          onSend={handleSendChat}
          open={chatOpen}
          onToggle={() => setChatOpen((v) => !v)}
        />
      </div>
    </div>
  );
}
