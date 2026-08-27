"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

interface LaunchButtonProps {
  href: string;
  label?: string;
  className?: string;
  onDone?: (data: { ok?: boolean; probe?: { reachable?: boolean; status?: string; message?: string }; message?: string }) => void;
}

export function LaunchButton({
  href,
  label = "Launch database",
  className = "btn btn-primary",
  onDone,
}: LaunchButtonProps) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  async function handleLaunch() {
    setLoading(true);
    setMessage(null);
    try {
      const res = await fetch(href, { method: "POST" });
      const data = (await res.json()) as {
        ok?: boolean;
        message?: string;
        probe?: { reachable?: boolean; status?: string; message?: string };
      };
      setMessage(data.message ?? data.probe?.message ?? (res.ok ? "Launch complete" : "Launch failed"));
      onDone?.(data);
      router.refresh();
    } catch {
      setMessage("Launch request failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <button type="button" className={className} onClick={handleLaunch} disabled={loading}>
        {loading ? "Launching…" : label}
      </button>
      {message && (
        <p className="muted text-sm mt-2">
          {message}
        </p>
      )}
    </div>
  );
}
