// Test harness: inject Supabase anon key into every request (Kong requires it).
// Points the official postgrest-js suite at the live backend as-is.
const ANON = process.env.ANON_KEY ?? "";
if (ANON) {
  const orig = globalThis.fetch;
  globalThis.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
    const headers = new Headers(init?.headers);
    if (!headers.has("apikey")) headers.set("apikey", ANON);
    if (!headers.has("Authorization")) headers.set("Authorization", "Bearer " + ANON);
    return orig(input, { ...init, headers });
  };
}
