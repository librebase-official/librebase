import type { Metadata } from "next";
import { LandingPage } from "@/components/landing/LandingPage";

export const metadata: Metadata = {
  title: "Librebase. A PostgreSQL platform that stays small and honest.",
  description:
    "PostgreSQL for apps and AI tools. Small footprint, sign-in by default, web interfaces, live updates, honest health status.",
  alternates: { canonical: "/" },
  openGraph: {
    title: "Librebase. A PostgreSQL platform that stays small and honest.",
    description:
      "Small footprint PostgreSQL platform. Sign-in by default. Honest health status. Waitlist for early access.",
    url: "/",
    type: "website",
  },
};

export default function MarketingHomePage() {
  return <LandingPage />;
}
