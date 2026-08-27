import type { Metadata } from "next";
import type { ReactNode } from "react";
import { SITE_URL } from "@/lib/site";

export const metadata: Metadata = {
  title: "Librebase for AI agents — connect via MCP",
  description:
    "Connect an AI agent to Librebase with a local MCP server. The user authenticates once in their browser (device flow); secrets stay sealed in the KMS and are redacted from the model.",
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
  featureList: [
    "MCP server for AI agents",
    "Browser device-flow auth (no API keys pasted)",
    "KMS-sealed secrets, redacted from the model",
    "Postgres projects, migrations, and instances",
    "OAuth (GitHub/Google) setup",
  ],
};

export default function ForAgentsPage() {
  return (
    <main
      style={{
        minHeight: "100vh",
        display: "flex",
        justifyContent: "center",
        padding: "48px 16px",
        background: "#0b0d12",
        color: "#e6e9ef",
        fontFamily: "system-ui, -apple-system, sans-serif",
      }}
    >
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <div style={{ maxWidth: 760, width: "100%" }}>
        <h1 style={{ fontSize: 28, margin: "0 0 8px" }}>Librebase for AI agents</h1>
        <p style={{ color: "#9aa4b2", marginTop: 0, fontSize: 15 }}>
          Connect an AI agent to Librebase with a local MCP server. The user
          authenticates once in their browser — no API keys are ever pasted, and
          secrets stay sealed in the KMS.
        </p>

        <Section title="1. Add the MCP server">
          <p>
            The MCP server is the <Code>mcp/</Code> directory of the Librebase
            repo. Add it to your agent&apos;s MCP config:
          </p>
          <pre
            style={{
              background: "#11141b",
              border: "1px solid #232838",
              borderRadius: 10,
              padding: 14,
              overflowX: "auto",
              fontSize: 13,
              lineHeight: 1.5,
            }}
          >
            <code>{JSON.stringify(mcpConfig, null, 2)}</code>
          </pre>
        </Section>

        <Section title="2. Authenticate (device flow)">
          <ol style={{ paddingLeft: 20, lineHeight: 1.7, margin: 0 }}>
            <li>
              Call <Code>auth_status</Code>. If unauthenticated, call{" "}
              <Code>auth_login</Code>.
            </li>
            <li>
              The user&apos;s browser opens{" "}
              <Code>{SITE_URL}/mcp/authorize?user_code=XXXX-XXXX</Code>.
            </li>
            <li>
              The user signs in (if needed) and clicks <b>Approve</b>. The token
              is stored in the OS keychain and is <b>never returned to the
              model</b>.
            </li>
          </ol>
        </Section>

        <Section title="3. What the agent can do">
          <ul style={{ paddingLeft: 20, lineHeight: 1.8, margin: 0 }}>
            <li>
              <Code>project_list</Code> / <Code>project_create</Code> /{" "}
              <Code>migration_apply</Code> / <Code>sql_execute</Code>
            </li>
            <li>
              <Code>key_list</Code> / <Code>key_create</Code> /{" "}
              <Code>key_get</Code> — secrets; the value is redacted from the
              model and stored locally
            </li>
            <li>
              <Code>auth_provider_upsert</Code> — OAuth (GitHub/Google); the
              client secret is KMS-sealed and never returned
            </li>
            <li>
              <Code>instance_list</Code> / <Code>instance_create</Code> /{" "}
              <Code>instance_launch</Code>
            </li>
          </ul>
        </Section>

        <Section title="Security">
          <ul style={{ paddingLeft: 20, lineHeight: 1.8, margin: 0 }}>
            <li>Secrets are sealed in the KMS; <Code>key_get</Code> hands the value to the process only.</li>
            <li>Every decrypt/sign is audited.</li>
            <li>Agent tokens are user-bound and revocable instantly.</li>
          </ul>
        </Section>

        <p style={{ color: "#6b7484", fontSize: 13, marginTop: 28 }}>
          Machine-readable version:{" "}
          <a href={`${SITE_URL}/llms.txt`} style={{ color: "#7aa2ff" }}>
            {SITE_URL}/llms.txt
          </a>
        </p>
      </div>
    </main>
  );
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section style={{ marginTop: 28 }}>
      <h2 style={{ fontSize: 17, margin: "0 0 10px", color: "#cdd4e0" }}>{title}</h2>
      {children}
    </section>
  );
}

function Code({ children }: { children: ReactNode }) {
  return (
    <code
      style={{
        background: "#181c26",
        padding: "1px 5px",
        borderRadius: 5,
        fontSize: 12.5,
        color: "#9ecbff",
      }}
    >
      {children}
    </code>
  );
}