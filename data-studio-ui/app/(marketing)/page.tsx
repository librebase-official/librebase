import type { Metadata } from "next";
import { LandingPage } from "@/components/landing/LandingPage";

/** Keep ≤60 chars so search + social cards do not truncate. */
const TITLE = "Librebase. Small, honest PostgreSQL.";
const DESCRIPTION =
  "PostgreSQL for apps and AI tools. Small footprint, sign-in by default, live updates, honest health status.";

export const metadata: Metadata = {
  // absolute: avoid "%s | Librebase" template pushing past ~60 chars
  title: { absolute: TITLE },
  description: DESCRIPTION,
  alternates: { canonical: "/" },
  openGraph: {
    title: TITLE,
    description: DESCRIPTION,
    url: "/",
    siteName: "Librebase",
    type: "website",
    locale: "en_US",
  },
  twitter: {
    card: "summary_large_image",
    title: TITLE,
    description: DESCRIPTION,
  },
};

export default function MarketingHomePage() {
  return <LandingPage />;
}
