/** Public console origin (app.librebase.xyz); marketing lives in librebase-landing. */
export const SITE_URL =
  process.env.NEXT_PUBLIC_SITE_URL?.replace(/\/$/, "") || "https://app.librebase.xyz";
