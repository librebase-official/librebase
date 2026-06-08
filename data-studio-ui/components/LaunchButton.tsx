"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

interface LaunchButtonProps {
  href: string;
  label?: string;
  className?: string;
}

export function LaunchButton({
  href,
  label = "Launch database",
  className = "btn btn-primary",
}: LaunchButtonProps) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  async function handleLaunch() {
    setLoading(true);
    setMessage(null);
    try {
      const res = await fetch(href, { method: "POST" });
      const data = (await res.json()) as { message?: string; probe?: { message?: string } };
      setMessage(data.message ?? data.probe?.message ?? (res.ok ? "Launch complete" : "Launch failed"));
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
        <p className="muted" style={{ marginTop: "0.5rem", fontSize: "0.85rem" }}>
          {message}
        </p>
      )}
    </div>
  );
}
