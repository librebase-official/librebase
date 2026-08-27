/**
 * Copy text to the clipboard with a fallback so it works even when the async
 * Clipboard API is unavailable or denied (non-secure contexts, permissions).
 * Returns true on success, false on failure.
 */
export async function copyText(text: string): Promise<boolean> {
  // Preferred: async Clipboard API (requires a secure context + permission).
  if (typeof navigator !== "undefined" && navigator.clipboard?.writeText) {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch {
      // fall through to the legacy path
    }
  }
  // Fallback: hidden textarea + execCommand (works broadly, incl. http).
  try {
    const textarea = document.createElement("textarea");
    textarea.value = text;
    textarea.setAttribute("readonly", "");
    textarea.style.position = "fixed";
    textarea.style.top = "-9999px";
    textarea.style.left = "-9999px";
    document.body.appendChild(textarea);
    textarea.select();
    textarea.setSelectionRange(0, text.length);
    const ok = document.execCommand("copy");
    document.body.removeChild(textarea);
    return ok;
  } catch {
    return false;
  }
}
