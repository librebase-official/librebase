import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: { default: "Librebase Admin", template: "%s | Librebase Admin" },
  description: "Internal SaaS admin dashboard for Librebase.",
  robots: { index: false, follow: false },
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" data-theme="dark">
      <body>{children}</body>
    </html>
  );
}
