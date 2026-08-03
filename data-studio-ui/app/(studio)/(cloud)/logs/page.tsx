import Link from "next/link";
import { readAccessLogTail, resolveAccessLogPath } from "@/lib/access-log";

export const dynamic = "force-dynamic";

export default async function LogsPage() {
  const filePath = resolveAccessLogPath();
  const lines = filePath ? readAccessLogTail(filePath, 100) : [];

  return (
    <div className="main" style={{ maxWidth: 960, margin: "2rem auto" }}>
      <div className="page-header">
        <div>
          <h1>Logs</h1>
          <p className="muted">
            Access-log tail (JSONL). Not Logflare — file sink from lis registry /
            <code>LIBREBASE_ACCESS_LOG</code>.
          </p>
        </div>
        <Link href="/projects" className="btn">
          Projects
        </Link>
      </div>

      <p className="muted" style={{ marginBottom: "1rem" }}>
        Source: {filePath ? <code>{filePath}</code> : "not configured"}
      </p>

      {lines.length === 0 ? (
        <p className="muted">No log lines yet.</p>
      ) : (
        <pre
          style={{
            fontSize: "0.8rem",
            overflow: "auto",
            maxHeight: "70vh",
            padding: "1rem",
            background: "var(--surface, #111)",
            border: "1px solid var(--border, #333)",
          }}
        >
          {lines
            .map((l) =>
              l.method
                ? `${l.ts ?? ""} ${l.method} ${l.path ?? ""} → ${l.status ?? ""}`
                : l.raw,
            )
            .join("\n")}
        </pre>
      )}
    </div>
  );
}
