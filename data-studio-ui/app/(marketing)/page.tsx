import type { Metadata } from "next";
import { LandingPage } from "@/components/landing/LandingPage";

export const metadata: Metadata = {
  title: "Librebase — Postgres platform. Honest status.",
  description:
    "Open data platform powered by lidb. Supabase-shaped Auth, REST, Realtime, and Studio with honest health.",
};

export default function MarketingHomePage() {
  return <LandingPage />;
}
