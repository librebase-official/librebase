import type { Metadata } from "next";
import { LandingPage } from "@/components/marketing/LandingPage";
import { SITE_URL } from "@/lib/site";

export const metadata: Metadata = {
  title: "Librebase — honest Postgres for builders and agents",
  description:
    "Postgres-compatible data layer with MCP, REST, and a studio that shows real health — not fake-green SaaS dashboards.",
  alternates: { canonical: `${SITE_URL}/landing` },
};

export default function MarketingLandingRoute() {
  return <LandingPage />;
}
