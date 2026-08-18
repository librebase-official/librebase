"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";

export function AcceptButton({ token }: { token: string }) {
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  const [err, setErr] = useState<string | null>(null);

  const accept = () =>
    startTransition(async () => {
      setErr(null);
      const res = await fetch(`/api/admin/invites/${token}/accept`, { method: "POST" });
      if (!res.ok) {
        const { error } = await res.json().catch(() => ({}));
        setErr(error || `Accept failed (${res.status})`);
        return;
      }
      const accepted = (await res.json()) as { orgId: string };
      const sw = await fetch("/api/admin/orgs/switch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ orgId: accepted.orgId }),
      });
      if (!sw.ok) {
        setErr(`Switch failed (${sw.status})`);
        return;
      }
      router.push("/projects");
      router.refresh();
    });

  return (
    <>
      <button type="button" className="btn btn-primary" disabled={pending} onClick={accept}>
        {pending ? "Accepting…" : "Accept invitation"}
      </button>
      {err ? <p className="auth-error">{err}</p> : null}
    </>
  );
}
