"use client";

import { useRef, useState } from "react";
import { copyText } from "@/lib/clipboard";

export function CopyField({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  const [state, setState] = useState<"idle" | "copied" | "failed">("idle");
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  async function copy() {
    const ok = await copyText(value);
    setState(ok ? "copied" : "failed");
    if (timer.current) clearTimeout(timer.current);
    timer.current = setTimeout(() => setState("idle"), 1500);
  }

  return (
    <div className="connect-row">
      {label ? <div className="connect-label">{label}</div> : null}
      <div className="connect-value">
        <code>{value}</code>
        <button
          type="button"
          className={`btn btn-ghost btn-sm${state === "copied" ? " btn-copied" : ""}`}
          aria-live="polite"
          onClick={copy}
        >
          {state === "copied" ? "Copied ✓" : state === "failed" ? "Failed" : "Copy"}
        </button>
      </div>
    </div>
  );
}
