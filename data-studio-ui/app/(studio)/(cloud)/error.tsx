"use client";

import { useEffect } from "react";

export default function StudioErrorBoundary({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Keep the console honest: log once, never swallow silently.
    console.error("Studio page error:", error);
  }, [error]);

  return (
    <div className="auth-page">
      <div className="auth-card">
        <p className="st-wordmark" style={{ border: 0, padding: 0, height: "auto", marginBottom: 16 }}>
          Libre<em>base</em>
        </p>
        <h1>Something went wrong</h1>
        <p className="muted">
          The console could not load this page — the backend may be briefly
          unavailable. Your data is safe; try again.
        </p>
        <button type="button" className="btn btn-primary" onClick={reset}>
          Try again
        </button>
      </div>
    </div>
  );
}