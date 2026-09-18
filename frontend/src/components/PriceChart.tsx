"use client";

import { useEffect, useRef } from "react";
import {
  AreaSeries,
  ColorType,
  CrosshairMode,
  createChart,
  type IChartApi,
  type ISeriesApi,
  type UTCTimestamp,
} from "lightweight-charts";

export interface PricePoint {
  time: string;
  value: number;
}

interface PriceChartProps {
  id: string;
  data: PricePoint[];
  variant?: "full" | "compact";
  color?: string;
}

function toSeriesPoint(point: PricePoint) {
  return {
    time: Math.floor(new Date(point.time).getTime() / 1000) as UTCTimestamp,
    value: point.value,
  };
}

export function PriceChart({ id, data, variant = "full", color = "#209dd7" }: PriceChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const seriesRef = useRef<ISeriesApi<"Area"> | null>(null);
  const lastIdRef = useRef(id);
  const lastLenRef = useRef(0);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const chart: IChartApi = createChart(container, {
      autoSize: true,
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: "#7d8598",
        fontFamily: "var(--font-mono)",
        fontSize: 11,
        // Keep the required TradingView attribution on full charts only; a sparkline
        // repeated per watchlist row shouldn't carry its own copy of the logo link.
        attributionLogo: variant === "full",
      },
      grid: {
        vertLines: { visible: false },
        horzLines: { color: "#1a2030", visible: variant === "full" },
      },
      rightPriceScale: { visible: variant === "full", borderColor: "#232a3a" },
      timeScale: {
        visible: variant === "full",
        borderColor: "#232a3a",
        timeVisible: true,
        secondsVisible: true,
      },
      crosshair: { mode: variant === "full" ? CrosshairMode.Normal : CrosshairMode.Hidden },
      handleScroll: variant === "full",
      handleScale: variant === "full",
    });

    const series = chart.addSeries(AreaSeries, {
      lineColor: color,
      topColor: `${color}33`,
      bottomColor: `${color}00`,
      lineWidth: 2,
      priceLineVisible: variant === "full",
      lastValueVisible: variant === "full",
      crosshairMarkerVisible: variant === "full",
    });

    seriesRef.current = series;
    lastLenRef.current = 0;

    return () => {
      chart.remove();
      seriesRef.current = null;
    };
  }, [variant, color]);

  useEffect(() => {
    const series = seriesRef.current;
    if (!series) return;

    if (id !== lastIdRef.current || data.length < lastLenRef.current) {
      series.setData(data.map(toSeriesPoint));
      lastIdRef.current = id;
      lastLenRef.current = data.length;
      return;
    }

    if (data.length > lastLenRef.current) {
      for (let i = lastLenRef.current; i < data.length; i += 1) {
        series.update(toSeriesPoint(data[i]));
      }
      lastLenRef.current = data.length;
    } else if (data.length > 0 && data.length === lastLenRef.current) {
      series.update(toSeriesPoint(data[data.length - 1]));
    }
  }, [id, data]);

  return <div ref={containerRef} className="h-full w-full" />;
}
