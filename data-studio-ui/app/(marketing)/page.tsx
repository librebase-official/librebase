import type { Metadata } from "next";
import { LandingPage } from "@/components/landing/LandingPage";
import { SITE_URL } from "@/lib/site";

/** Keep ≤60 chars so search + social cards do not truncate. */
const TITLE = "Librebase. Small, honest PostgreSQL.";
const DESCRIPTION =
  "PostgreSQL for apps and AI tools. Small footprint, sign-in by default, live updates, honest health status.";

/** Static PNG — X/Twitterbot often fails on Next chunked ImageResponse routes. */
const OG_IMAGE = {
  url: `${SITE_URL}/og.png`,
  width: 1200,
  height: 630,
  alt: "Librebase: a PostgreSQL platform that stays small and honest.",
  type: "image/png",
} as const;

export const metadata: Metadata = {
  // absolute: avoid "%s | Librebase" template pushing past ~60 chars
  title: { absolute: TITLE },
  description: DESCRIPTION,
  alternates: { canonical: "/" },
  openGraph: {
    title: TITLE,
    description: DESCRIPTION,
    url: SITE_URL,
    siteName: "Librebase",
    type: "website",
    locale: "en_US",
    images: [OG_IMAGE],
  },
  twitter: {
    card: "summary_large_image",
    title: TITLE,
    description: DESCRIPTION,
    images: [OG_IMAGE.url],
  },
};

export default function MarketingHomePage() {
  return <LandingPage />;
}
