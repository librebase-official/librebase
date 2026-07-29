import type { Metadata } from "next";
import { LandingPage } from "@/components/landing/LandingPage";

export const metadata: Metadata = {
  title: "Librebase. A PostgreSQL platform that stays small and honest.",
  description:
    "PostgreSQL for apps and AI tools. Aiming for ~64 MB RAM and Supabase-class speed on the core path, strong sign-in defaults, web interfaces, live updates, and a console that shows real status.",
  alternates: { canonical: "/" },
  openGraph: {
    title: "Librebase. A PostgreSQL platform that stays small and honest.",
    description:
      "Aiming for ~64 MB RAM and Supabase-class core-path speed. Honest health status. Waitlist for early access.",
    url: "/",
    type: "website",
  },
};

export default function MarketingHomePage() {
  return <LandingPage />;
}
