import type { Metadata } from "next";
import { Orbitron, Space_Grotesk, IBM_Plex_Mono } from "next/font/google";
import { SITE_URL } from "@/lib/site";
import "./globals.css";

const LIBREBASE_VERSION = "0.1.9";

const THEME_BOOT =
  "(function(){try{var q=new URLSearchParams(location.search).get('theme');var t=q==='dark'||q==='light'?q:localStorage.getItem('lb-studio-theme');if(t!=='dark'&&t!=='light'){t=window.matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light';}document.documentElement.setAttribute('data-theme',t);if(q==='dark'||q==='light'){localStorage.setItem('lb-studio-theme',t);}}catch(e){}})();";

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
      data-theme="light"
      suppressHydrationWarning
      className={`${orbitron.variable} ${spaceGrotesk.variable} ${plexMono.variable}`}
    >
      <head>
        <script dangerouslySetInnerHTML={{ __html: THEME_BOOT }} />
      </head>
      <body>
        {children}
        <footer className="lb-footer">
          <span className="lb-footer-links">
            Librebase v{LIBREBASE_VERSION}
          </span>
        </footer>
      </body>
    </html>
  );
}
