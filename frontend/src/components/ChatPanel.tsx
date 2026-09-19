"use client";

import { useState, type FormEvent } from "react";
import type { ChatMessage } from "@/lib/types";

interface ChatPanelProps {
  messages: ChatMessage[];
  loading: boolean;
  onSend: (message: string) => Promise<void>;
  open: boolean;
  onToggle: () => void;
}

export function ChatPanel({ messages, loading, onSend, open, onToggle }: ChatPanelProps) {
  const [draft, setDraft] = useState("");

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    const text = draft.trim();
    if (!text || loading) return;
    setDraft("");
    await onSend(text);
  };

  if (!open) {
    return (
      <button
        type="button"
        onClick={onToggle}
        aria-label="Open AI chat"
        className="flex h-full w-10 shrink-0 flex-col items-center gap-2 border-l border-border bg-panel py-4 text-text-muted hover:text-text"
      >
        <span className="[writing-mode:vertical-rl]">AI chat</span>
      </button>
    );
  }

  return (
    <div className="flex h-full w-96 shrink-0 flex-col border-l border-border bg-panel">
      <div className="flex items-center justify-between border-b border-border px-3 py-2">
        <span className="text-sm font-medium text-text">FinAlly assistant</span>
        <button
          type="button"
          onClick={onToggle}
          aria-label="Collapse AI chat"
          className="text-text-muted hover:text-text"
        >
          ×
        </button>
      </div>
      <div className="flex-1 space-y-3 overflow-y-auto px-3 py-3">
        {messages.length === 0 && (
          <p className="text-sm text-text-muted">
            Ask about your portfolio, or tell it to make a trade.
          </p>
        )}
        {messages.map((message) => (
          <div
            key={message.id}
            data-testid={`chat-message-${message.role}`}
            className={message.role === "user" ? "ml-6" : "mr-6"}
          >
            <div
              className={`border px-3 py-2 text-sm ${
                message.role === "user"
                  ? "border-blue/40 bg-blue/10 text-text"
                  : "border-border bg-panel-raised text-text"
              }`}
            >
              {message.content}
            </div>
            {message.actions?.trades?.map((trade, i) => (
              <div key={`t-${i}`} className="mt-1 ml-1 font-mono text-xs text-yellow">
                Executed: {trade.side} {trade.quantity} {trade.ticker}
              </div>
            ))}
            {message.actions?.watchlist_changes?.map((change, i) => (
              <div key={`w-${i}`} className="mt-1 ml-1 font-mono text-xs text-yellow">
                Watchlist: {change.action === "add" ? "added" : "removed"} {change.ticker}
              </div>
            ))}
          </div>
        ))}
        {loading && (
          <div data-testid="chat-loading" role="status" className="text-sm text-text-muted">
            FinAlly is thinking…
          </div>
        )}
      </div>
      <form onSubmit={submit} className="flex gap-2 border-t border-border p-2">
        <input
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          placeholder="Message FinAlly"
          aria-label="Chat message"
          className="min-w-0 flex-1 border border-border bg-bg px-2 py-1.5 text-sm text-text placeholder:text-text-muted focus:border-blue focus:outline-none"
        />
        <button
          type="submit"
          disabled={loading}
          className="bg-purple px-3 py-1.5 text-sm font-medium text-text disabled:opacity-50"
        >
          Send
        </button>
      </form>
    </div>
  );
}
