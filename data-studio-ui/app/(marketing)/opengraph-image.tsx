import { ImageResponse } from "next/og";

export const alt =
  "Librebase: a PostgreSQL platform that stays small and honest.";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

async function loadFont(family: string, weight: number): Promise<ArrayBuffer> {
  const css = await fetch(
    `https://fonts.googleapis.com/css2?family=${encodeURIComponent(family)}:wght@${weight}&display=swap`,
    { headers: { "User-Agent": "Mozilla/5.0" } },
  ).then((r) => r.text());
  const match = css.match(/src: url\(([^)]+)\) format\('(opentype|truetype|woff2?)'\)/);
  if (!match?.[1]) {
    throw new Error(`Font URL not found for ${family} ${weight}`);
  }
  return fetch(match[1]).then((r) => r.arrayBuffer());
}

export default async function OpenGraphImage() {
  const [display, body] = await Promise.all([
    loadFont("Orbitron", 700),
    loadFont("Space Grotesk", 500),
  ]);

  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          position: "relative",
          overflow: "hidden",
          background: "linear-gradient(165deg, #0a1618 0%, #071014 48%, #050c0e 100%)",
          color: "#e7f2ec",
          fontFamily: "Space Grotesk",
        }}
      >
        {/* Atmosphere */}
        <div
          style={{
            position: "absolute",
            right: -80,
            top: -120,
            width: 640,
            height: 640,
            borderRadius: 9999,
            background:
              "radial-gradient(circle, rgba(47,212,194,0.28) 0%, rgba(47,212,194,0.08) 42%, transparent 70%)",
          }}
        />
        <div
          style={{
            position: "absolute",
            left: -160,
            bottom: -200,
            width: 520,
            height: 520,
            borderRadius: 9999,
            background:
              "radial-gradient(circle, rgba(31,168,154,0.18) 0%, transparent 68%)",
          }}
        />

        {/* Soft grid */}
        <div
          style={{
            position: "absolute",
            inset: 0,
            opacity: 0.18,
            backgroundImage:
              "linear-gradient(rgba(231,242,236,0.08) 1px, transparent 1px), linear-gradient(90deg, rgba(231,242,236,0.08) 1px, transparent 1px)",
            backgroundSize: "48px 48px",
          }}
        />

        {/* Content */}
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            justifyContent: "space-between",
            width: "100%",
            height: "100%",
            padding: "64px 72px",
            position: "relative",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
            <div
              style={{
                width: 14,
                height: 14,
                borderRadius: 9999,
                background: "#2fd4c2",
                boxShadow: "0 0 24px rgba(47,212,194,0.85)",
              }}
            />
            <div
              style={{
                fontFamily: "Orbitron",
                fontSize: 42,
                letterSpacing: "0.04em",
                display: "flex",
              }}
            >
              Libre
              <span style={{ color: "#2fd4c2" }}>base</span>
            </div>
          </div>

          <div style={{ display: "flex", gap: 48, alignItems: "flex-end" }}>
            <div style={{ display: "flex", flexDirection: "column", flex: 1, gap: 22 }}>
              <div
                style={{
                  fontFamily: "Orbitron",
                  fontSize: 56,
                  lineHeight: 1.12,
                  letterSpacing: "-0.02em",
                  maxWidth: 640,
                }}
              >
                A PostgreSQL platform that stays small and honest.
              </div>
              <div
                style={{
                  fontSize: 26,
                  color: "#9bb0aa",
                  maxWidth: 560,
                  lineHeight: 1.35,
                }}
              >
                Lean footprint. Sign-in by default. Honest health status.
              </div>
              <div style={{ display: "flex", gap: 12, marginTop: 8 }}>
                {["Postgres-shaped", "Agent-ready", "Real status"].map((label) => (
                  <div
                    key={label}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      padding: "10px 18px",
                      borderRadius: 9999,
                      border: "1px solid rgba(231,242,236,0.14)",
                      background: "rgba(14,26,28,0.72)",
                      color: "#9bb0aa",
                      fontSize: 18,
                    }}
                  >
                    {label}
                  </div>
                ))}
              </div>
            </div>

            {/* Mini console panel */}
            <div
              style={{
                width: 360,
                display: "flex",
                flexDirection: "column",
                borderRadius: 18,
                border: "1px solid rgba(231,242,236,0.14)",
                background: "rgba(14,26,28,0.88)",
                padding: "28px 28px 32px",
                gap: 14,
                boxShadow: "0 24px 64px rgba(0,0,0,0.35)",
              }}
            >
              <div style={{ display: "flex", gap: 8 }}>
                <div style={{ width: 10, height: 10, borderRadius: 9999, background: "#e8a838" }} />
                <div style={{ width: 10, height: 10, borderRadius: 9999, background: "#9bb0aa" }} />
                <div style={{ width: 10, height: 10, borderRadius: 9999, background: "#2fd4c2" }} />
              </div>
              <div style={{ fontSize: 20, color: "#2fd4c2", fontFamily: "Space Grotesk" }}>
                select * from parity_items
              </div>
              <div style={{ fontSize: 18, color: "#9bb0aa" }}>where owner_id = auth.uid()</div>
              <div
                style={{
                  marginTop: 10,
                  height: 3,
                  width: "70%",
                  borderRadius: 9999,
                  background:
                    "linear-gradient(90deg, transparent, #2fd4c2 40%, transparent)",
                }}
              />
            </div>
          </div>

          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              color: "#9bb0aa",
              fontSize: 22,
            }}
          >
            <div style={{ display: "flex" }}>librebase.xyz</div>
            <div style={{ display: "flex", color: "#2fd4c2" }}>Join the waitlist</div>
          </div>
        </div>
      </div>
    ),
    {
      ...size,
      fonts: [
        { name: "Orbitron", data: display, style: "normal", weight: 700 },
        { name: "Space Grotesk", data: body, style: "normal", weight: 500 },
      ],
    },
  );
}
