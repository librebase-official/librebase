import { NextResponse } from "next/server";

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export async function POST(req: Request) {
  let body: { email?: string; source?: string };
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ ok: false, error: "invalid_json" }, { status: 400 });
  }

  const email = String(body.email ?? "")
    .trim()
    .toLowerCase();
  if (!EMAIL_RE.test(email)) {
    return NextResponse.json({ ok: false, error: "invalid_email" }, { status: 400 });
  }

  const url = process.env.LIBREBASE_SUPABASE_URL ?? process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key =
    process.env.LIBREBASE_SUPABASE_SERVICE_ROLE_KEY ??
    process.env.SUPABASE_SERVICE_ROLE_KEY;

  if (!url || !key) {
    return NextResponse.json(
      { ok: false, error: "waitlist_not_configured" },
      { status: 503 },
    );
  }

  const res = await fetch(`${url.replace(/\/$/, "")}/rest/v1/librebase_waitlist`, {
    method: "POST",
    headers: {
      apikey: key,
      Authorization: `Bearer ${key}`,
      "Content-Type": "application/json",
      Prefer: "return=minimal,resolution=ignore-duplicates",
    },
    body: JSON.stringify({
      email,
      source: body.source ?? "landing",
    }),
  });

  if (!res.ok) {
    const text = await res.text();
    return NextResponse.json(
      { ok: false, error: "supabase_error", detail: text.slice(0, 200) },
      { status: 502 },
    );
  }

  return NextResponse.json({ ok: true });
}
