import { afterEach, describe, expect, it, vi } from "vitest";

import { POST } from "@/app/api/admin-proxy/[...path]/route";

const UPSTREAM = "http://admin.internal:54330";

function env(vars: Record<string, string>) {
  for (const [k, v] of Object.entries(vars)) process.env[k] = v;
}

function post(
  segments: string[],
  init: { body?: string; headers?: HeadersInit } = {},
) {
  return POST(
    new Request(
      `http://console.test/api/admin-proxy/${segments.join("/")}`,
      {
        method: "POST",
        headers: init.headers,
        body: init.body,
      },
    ),
    { params: Promise.resolve({ path: segments }) },
  );
}

afterEach(() => {
  delete process.env.LIBREBASE_ADMIN_URL;
  vi.unstubAllGlobals();
});

describe("admin-proxy webhook ingress", () => {
  it("forwards the raw body and required headers to the allowlisted path", async () => {
    env({ LIBREBASE_ADMIN_URL: UPSTREAM });
    const upstream = vi.fn().mockResolvedValue(
      new Response('{"received":true}', {
        status: 200,
        headers: { "content-type": "application/json" },
      }),
    );
    vi.stubGlobal("fetch", upstream);

    const body = JSON.stringify({
      id: "evt_1",
      type: "checkout.session.completed",
    });
    const res = await post(["org", "v1", "billing", "webhook"], {
      body,
      headers: {
        "content-type": "application/json",
        "stripe-signature": "t=1,v1=abc",
      },
    });

    expect(res.status).toBe(200);
    expect(await res.text()).toBe('{"received":true}');
    expect(upstream).toHaveBeenCalledTimes(1);
    const [url, init] = upstream.mock.calls[0] as [string, RequestInit];
    expect(url).toBe(`${UPSTREAM}/org/v1/billing/webhook`);
    expect(init.method).toBe("POST");
    // The raw bytes must pass through untouched (Stripe signs the exact body).
    expect(new TextDecoder().decode(init.body as ArrayBuffer)).toBe(body);
    expect((init.headers as Headers).get("stripe-signature")).toBe("t=1,v1=abc");
  });

  it("rejects paths not on the allowlist", async () => {
    env({ LIBREBASE_ADMIN_URL: UPSTREAM });
    const upstream = vi.fn();
    vi.stubGlobal("fetch", upstream);

    const res = await post(["org", "v1", "orgs", "org_x", "instances"], {
      body: "{}",
    });

    expect(res.status).toBe(404);
    expect(upstream).not.toHaveBeenCalled();
  });

  it("rejects traversal / malformed segments", async () => {
    env({ LIBREBASE_ADMIN_URL: UPSTREAM });
    const upstream = vi.fn();
    vi.stubGlobal("fetch", upstream);

    expect((await post(["org", "..", "v1", "billing", "webhook"])).status).toBe(400);
    expect((await post([".."])).status).toBe(400);
    expect((await post([])).status).toBe(400);
    expect(upstream).not.toHaveBeenCalled();
  });

  it("returns 503 when admin api is disabled", async () => {
    const res = await post(["org", "v1", "billing", "webhook"], { body: "{}" });
    expect(res.status).toBe(503);
  });

  it("maps upstream failure to 502", async () => {
    env({ LIBREBASE_ADMIN_URL: UPSTREAM });
    const upstream = vi.fn().mockRejectedValue(new Error("refused"));
    vi.stubGlobal("fetch", upstream);

    const res = await post(["org", "v1", "billing", "webhook"], { body: "{}" });
    expect(res.status).toBe(502);
  });

  it("passes through upstream error status", async () => {
    env({ LIBREBASE_ADMIN_URL: UPSTREAM });
    const upstream = vi.fn().mockResolvedValue(
      new Response('{"error":"invalid stripe signature"}', {
        status: 401,
        headers: { "content-type": "application/json" },
      }),
    );
    vi.stubGlobal("fetch", upstream);

    const res = await post(["org", "v1", "billing", "webhook"], { body: "{}" });
    expect(res.status).toBe(401);
    expect(await res.json()).toEqual({ error: "invalid stripe signature" });
  });
});
