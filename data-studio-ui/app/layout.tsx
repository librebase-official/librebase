import type { Metadata } from "next";
import { Orbitron, Space_Grotesk, IBM_Plex_Mono } from "next/font/google";
import { SITE_URL } from "@/lib/site";
import "./globals.css";

/** Display: hero + wordmark only — do not use for every heading. */
const orbitron = Orbitron({
  subsets: ["latin"],
  variable: "--font-display",
  display: "swap",
});

const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-body",
  display: "swap",
});

const plexMono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "500"],
  variable: "--font-mono",
  display: "swap",
});

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: "Librebase Console",
    template: "%s | Librebase",
  },
  description:
    "Librebase console — manage your PostgreSQL projects, instances, and providers.",
  robots: {
    index: false,
    follow: false,
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${orbitron.variable} ${spaceGrotesk.variable} ${plexMono.variable}`}
    >
      <body>{children}</body>
    </html>
  );
}
