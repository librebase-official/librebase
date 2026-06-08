import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Librebase Studio",
  description: "Org, project, and database console for Librebase",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
