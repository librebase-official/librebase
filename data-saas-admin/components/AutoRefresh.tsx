"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";

interface Props {
  /** Poll interval in ms. Default 15 000 (15s). */
  interval?: number;
}

export function AutoRefresh({ interval = 15_000 }: Props) {
  const router = useRouter();
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());
  const [paused, setPaused] = useState(false);
  const timer = useRef<ReturnType<typeof setInterval>>(undefined);

  useEffect(() => {
    if (paused) return;
    timer.current = setInterval(() => {
      router.refresh();
      setLastRefresh(new Date());
    }, interval);
    return () => clearInterval(timer.current);
  }, [interval, paused, router]);

  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 12, color: "var(--muted)" }}>
      <span
        style={{
          width: 6, height: 6, borderRadius: "50%",
          background: paused ? "var(--muted)" : "var(--success)",
          display: "inline-block",
        }}
      />
      {paused ? "paused" : `refreshing every ${interval / 1000}s`}
      <span style={{ marginLeft: 4 }}>
        last: {lastRefresh.toLocaleTimeString()}
      </span>
      <button
        className="btn btn-sm"
        onClick={() => {
          setPaused((p) => !p);
          if (paused) {
            router.refresh();
            setLastRefresh(new Date());
          }
        }}
      >
        {paused ? "resume" : "pause"}
      </button>
    </div>
  );
}
