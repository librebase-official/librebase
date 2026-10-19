import type { Metadata } from "next";
import type { ReactNode } from "react";
import Link from "next/link";
import { BrandWordmark } from "@/components/brand/BrandWordmark";
import {
  HOSTED_MCP_TOOL_COUNT,
  HOSTED_MCP_TOOL_DOC_GROUPS,
} from "@/lib/hosted-mcp-tool-docs";
import { SITE_URL } from "@/lib/site";

export const metadata: Metadata = {
  title: "Librebase for AI agents — connect via MCP",
  description:
    "Connect an AI agent to Librebase with hosted remote MCP and browser authorization; secrets stay sealed in the KMS and are redacted from the model.",
  robots: { index: true, follow: true },
  alternates: { canonical: `${SITE_URL}/for-agents` },
};

const mcpConfig = {
  mcpServers: {
    librebase: {
      command: "python3",
      args: ["-m", "librebase_mcp"],
      env: {
        LIBREBASE_ADMIN_URL: `${SITE_URL}/api/admin-proxy`,
        LIBREBASE_CONSOLE_URL: SITE_URL,
      },
    },
  },
};

const jsonLd = {
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  name: "Librebase",
  description:
    "Open-source Postgres app platform. AI agents manage projects, instances, auth, and secrets through a local MCP server; the user authenticates once in their browser.",
  url: SITE_URL,
  applicationCategory: "DeveloperApplication",
  operatingSystem: "Any",
  offers: { "@type": "Offer", price: "0", priceCurrency: "USD" },
};

export default function ForAgentsPage() {
  return (
    <div className="lb-landing is-ready lb-doc">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <header className="lb-nav">
        <BrandWordmark href="/landing" variant="marketing" size="md" />
        <div className="lb-nav-actions">
          <Link className="lb-link-quiet" href="/landing">Home</Link>
          <Link className="lb-link-quiet" href="/design">Design</Link>
          <Link className="lb-btn lb-btn-ghost" href="/login">Sign in</Link>
          <Link className="lb-btn lb-btn-primary" href="/setup">Get started</Link>
        </div>
      </header>

      <article className="lb-doc-main">
        <p className="lb-brand-signal">MCP · device flow · KMS-sealed secrets</p>
        <h1 className="lb-doc-title">Librebase for AI agents</h1>
        <p className="lb-doc-lead">
          Connect an AI agent with hosted remote MCP. The user authenticates once in the browser — no API keys pasted,
          and secrets stay sealed in the KMS.
        </p>

        <Section title="1. Connect via hosted MCP (no install)">
          <p>
            Point your remote MCP-capable agent at <Code>{SITE_URL}/api/mcp</Code> — no local repo or pasted key needed.
          </p>
          <pre className="lb-doc-pre">
            <code>{`{
  "mcpServers": {
    "librebase": {
      "url": "${SITE_URL}/api/mcp",
      "auth": {
        "authorization_server": "${SITE_URL}/.well-known/oauth-authorization-server",
        "scopes": ["mcp"]
      }
    }
  }
}`}</code>
          </pre>
          <p className="lb-doc-muted">
            Or use auto-discovery: <Code>GET /.well-known/mcp.json</Code>
          </p>
        </Section>

        <Section title="1b. Optional: run locally for CI or air-gapped use">
          <pre className="lb-doc-pre">
            <code>{JSON.stringify(mcpConfig, null, 2)}</code>
          </pre>
        </Section>

        <Section title="2. Authenticate (device flow)">
          <ol className="lb-doc-list">
            <li>Call <Code>auth_start</Code>, then <Code>auth_poll</Code> until approval completes.</li>
            <li>Browser opens <Code>{SITE_URL}/mcp/authorize?user_code=XXXX-XXXX</Code>.</li>
            <li>User approves; token stays in the OS keychain and is never returned to the model.</li>
          </ol>
        </Section>

        <Section title={`3. Hosted MCP tools (${HOSTED_MCP_TOOL_COUNT})`}>
          <p className="lb-doc-muted" style={{ marginBottom: "0.75rem" }}>
            Source of truth: <Code>POST /api/mcp</Code> → <Code>tools/list</Code>. Full audit:{" "}
            <Code>docs/mcp/AUDIT.md</Code> in the repo.
          </p>
          <ul className="lb-doc-list">
            {HOSTED_MCP_TOOL_DOC_GROUPS.map((group) => (
              <li key={group.names.join("-")}>
                {group.names.map((name, i) => (
                  <span key={name}>
                    {i > 0 ? (group.llmsJoin === "/" ? " / " : ", ") : null}
                    <Code>{name}</Code>
                  </span>
                ))}
                {group.forAgentsNote ? ` — ${group.forAgentsNote}` : null}
              </li>
            ))}
          </ul>
        </Section>

        <p className="lb-doc-muted lb-doc-foot">
          Machine-readable:{" "}
          <a href={`${SITE_URL}/llms.txt`} className="lb-doc-link">
            {SITE_URL}/llms.txt
          </a>
        </p>
      </article>
    </div>
  );
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="lb-doc-section">
      <h2 className="lb-doc-h2">{title}</h2>
      {children}
    </section>
  );
}

function Code({ children }: { children: ReactNode }) {
  return <code className="lb-doc-code">{children}</code>;
}
