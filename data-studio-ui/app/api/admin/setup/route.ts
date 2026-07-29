import { NextResponse } from "next/server";
import { adminSetup, adminApiEnabled } from "@/lib/librebase-admin-client";

export async function POST(request: Request) {
  if (!adminApiEnabled()) {
    return NextResponse.json(
      {
        error:
          "Admin API disabled — set LIBREBASE_ADMIN_URL (e.g. http://127.0.0.1:54330)",
      },
      { status: 503 },
    );
  }
  try {
    const body = (await request.json()) as {
      name?: string;
      ownerEmail?: string;
      password?: string;
      slug?: string;
    };
    if (!body.name?.trim() || !body.ownerEmail?.trim() || !body.password) {
      return NextResponse.json(
        { error: "name, ownerEmail, password required" },
        { status: 400 },
      );
    }
    const result = await adminSetup({
      name: body.name.trim(),
      ownerEmail: body.ownerEmail.trim(),
      password: body.password,
      slug: body.slug,
    });
    // Persist session for subsequent server calls in this process (dev).
    process.env.LIBREBASE_ADMIN_SESSION = result.token;
    process.env.LIBREBASE_ORG_ID = result.orgId;
    return NextResponse.json(result, { status: 201 });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Setup failed";
    const status = message.includes("409") || message.includes("already") ? 409 : 500;
    return NextResponse.json({ error: message }, { status });
  }
}
