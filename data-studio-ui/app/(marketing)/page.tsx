import type { Metadata } from "next";
import { LandingPage } from "@/components/landing/LandingPage";

export const metadata: Metadata = {
  title: "Librebase. A PostgreSQL platform that stays small and honest.",
  description:
    "PostgreSQL for apps and AI tools. Low memory, strong sign-in defaults, web interfaces, live updates, and a console that shows real status.",
};

export default function MarketingHomePage() {
  return <LandingPage />;
}
