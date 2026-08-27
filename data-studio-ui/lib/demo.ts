/** Public demo project used by /demo/feedback. */
export const DEMO_PROJECT_ID =
  process.env.NEXT_PUBLIC_DEMO_PROJECT_ID || "proj_16ddfd2e9733";

export const DEMO_API_URL =
  process.env.NEXT_PUBLIC_DEMO_API_URL ||
  process.env.NEXT_PUBLIC_FEEDBACK_URL ||
  "https://feedback.librebase.xyz";

/** Public wall origin (OAuth redirect_to / GitHub homepage). */
export const FEEDBACK_ORIGIN =
  process.env.NEXT_PUBLIC_FEEDBACK_URL || "https://feedback.librebase.xyz";
