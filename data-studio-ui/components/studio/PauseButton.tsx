"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

export function PauseButton({
  href,
  label = "Pause",
  className = "btn btn-sm",
  onDone,
}: {
  href: string;
  label?: string;
  className?: string;
  onDone?: (data: { ok?: boolean; probe?: { reachable?: boolean; status?: string; message?: string }; message?: string }) => void;
}) {
  const router = useRouter();
  const [pending, setPending] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  async function pause() {
    setPending(true);
    setMessage(null);
    try {
      const res = await fetch(href, { method: "POST" });
      const body = (await res.json()) as {
        ok?: boolean;
        message?: string;
        error?: string;
        probe?: { reachable?: boolean; status?: string; message?: string };
      };
      setMessage(body.message ?? body.error ?? (res.ok ? "Paused" : "Pause failed"));
      onDone?.(body);
      router.refresh();
    } catch {
      setMessage("Pause request failed");
    } finally {
      setPending(false);
    }
  }

  return (
    <div>
      <button type="button" className={className} onClick={pause} disabled={pending}>
        {pending ? "Pausing…" : label}
      </button>
      {message ? <p className="muted text-sm mt-2">{message}</p> : null}
    </div>
  );
}
