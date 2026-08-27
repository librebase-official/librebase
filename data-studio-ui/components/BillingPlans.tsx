"use client";

import { useState, useTransition } from "react";
import { Button } from "@/components/ui";

interface BillingPlansProps {
  orgId: string;
  plan: string;
  edition: string;
  stripeConfigured: boolean;
  stripeStatus?: string | null;
  instanceCount: number;
  instanceLimit: number;
}

const PLANS = [
  { id: "starter" as const, label: "Starter", price: "$29" },
  { id: "pro" as const, label: "Pro", price: "$69" },
  { id: "scale" as const, label: "Scale", price: "Usage" },
];

export function BillingPlans(props: BillingPlansProps) {
  const [error, setError] = useState<string | null>(null);
  const [pending, start] = useTransition();

  const go = (path: string, body?: unknown) => {
    start(async () => {
      setError(null);
      const res = await fetch(path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: body !== undefined ? JSON.stringify(body) : "{}",
      });
      const data = (await res.json().catch(() => ({}))) as { url?: string; error?: string };
      if (!res.ok || !data.url) {
        setError(data.error || "Billing request failed");
        return;
      }
      window.location.href = data.url;
    });
  };

  return (
    <section className="admin-section">
      <h2 className="admin-section-title">Billing</h2>
      <p className="muted">
        Plan <strong>{props.plan}</strong> · edition {props.edition}
        {props.stripeStatus ? ` · Stripe ${props.stripeStatus}` : ""} · {props.instanceCount}/
        {props.instanceLimit === 0 ? "∞" : props.instanceLimit} instances
      </p>
      {!props.stripeConfigured && (
        <p className="auth-error">Stripe is not configured on this control plane.</p>
      )}
      <div className="action-row" style={{ marginTop: 12 }}>
        {PLANS.map((plan) => (
          <Button
            key={plan.id}
            variant={props.plan === plan.id ? "primary" : "ghost"}
            size="sm"
            disabled={pending || !props.stripeConfigured || props.plan === plan.id}
            onClick={() => go("/api/admin/billing/session", { plan: plan.id })}
          >
            {plan.label} {plan.price}
          </Button>
        ))}
        <Button
          variant="ghost"
          size="sm"
          disabled={pending || !props.stripeConfigured}
          onClick={() => go("/api/admin/billing/portal")}
        >
          Manage subscription
        </Button>
      </div>
      {error && <p className="auth-error">{error}</p>}
    </section>
  );
}
