import type { Metadata } from "next";
import type { ReactNode } from "react";
import Link from "next/link";
import { BrandWordmark } from "@/components/brand/BrandWordmark";
import { SITE_URL } from "@/lib/site";

export const metadata: Metadata = {
  title: "Librebase for AI agents — connect via MCP",
  description:
    "Connect an AI agent to Librebase's hosted MCP with a browser device-flow sign-in; KMS secret values are only returned by key_decrypt.",
  robots: { index: true, follow: true },
  alternates: { canonical: `${SITE_URL}/for-agents` },
};

// Keep in sync with the live `POST /api/mcp` -> `tools/list` (LIB-149).
const mcpConfig = {
  mcpServers: {
    librebase: {
      type: "http",
      url: `${SITE_URL}/api/mcp`,
      headers: { Authorization: "Bearer <lb_agt_ token from auth_poll>" },
    },
  },
};

const jsonLd = {
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  name: "Librebase",
  description:
    "Open-source Postgres app platform. AI agents manage projects, instances, members, hosts, and KMS secrets through a hosted MCP server; a human approves the agent once in the browser.",
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
        <p className="lb-brand-signal">Hosted MCP · device flow · KMS-sealed secrets</p>
        <h1 className="lb-doc-title">Librebase for AI agents</h1>
        <p className="lb-doc-lead">
          Connect an AI agent to the hosted MCP server. The agent starts a device flow, a human approves it once in the
          browser, and the agent sends the resulting token as a Bearer header.
        </p>

        <Section title="1. Sign in (device flow)">
          <ol className="lb-doc-list">
            <li>
              Call <Code>auth_start</Code> on <Code>{SITE_URL}/api/mcp</Code>. No token is needed. It returns a{" "}
              <Code>userCode</Code> and a link valid for 30 minutes.
            </li>
            <li>
              The human opens <Code>{SITE_URL}/mcp/authorize?user_code=XXXX-XXXX</Code>, signs in with Google or
              GitHub, and clicks Approve.
            </li>
            <li>
              Call <Code>auth_poll</Code> with the <Code>deviceCode</Code> every 5 seconds until it returns an{" "}
              <Code>accessToken</Code> (<Code>lb_agt_…</Code>). Keep it out of chat.
            </li>
          </ol>
        </Section>

        <Section title="2. Call the hosted MCP">
          <p>
            Send the token as <Code>Authorization: Bearer …</Code> to <Code>{SITE_URL}/api/mcp</Code>. Without it, every
            tool except <Code>auth_start</Code> and <Code>auth_poll</Code> answers HTTP 401.
          </p>
          <pre className="lb-doc-pre">
            <code>{JSON.stringify(mcpConfig, null, 2)}</code>
          </pre>
          <p className="lb-doc-muted">
            Not live yet: automatic OAuth connect cards in MCP clients, and PyPI/npm packages. The Python stdio server
            (<Code>python3 -m librebase_mcp</Code>) runs only from a repo checkout and has a subset of the tools.
          </p>
          <p className="lb-doc-muted">
            Auth failures return an explicit <Code>cause</Code> (<Code>revoked</Code>, <Code>expired</Code>,{" "}
            <Code>unknown_token</Code>, …) instead of a generic org-resolution error.
          </p>
        </Section>

        <Section title="3. Hosted MCP tools (27)">
          <p className="lb-doc-muted" style={{ marginBottom: "0.75rem" }}>
            Source of truth: <Code>POST /api/mcp</Code> → <Code>tools/list</Code>.
          </p>
          <ul className="lb-doc-list">
            <li>
              <Code>org_whoami</Code>, <Code>project_list</Code>, <Code>project_create</Code>
            </li>
            <li>
              <Code>auth_provider_list</Code>, <Code>auth_provider_upsert</Code> — client secret is KMS-sealed, never
              returned
            </li>
            <li>
              <Code>instance_list</Code>, <Code>instance_get</Code>, <Code>instance_create</Code>,{" "}
              <Code>instance_launch</Code>, <Code>instance_stop</Code>
            </li>
            <li>
              <Code>member_list</Code>, <Code>member_invite</Code>, <Code>member_update_role</Code>
            </li>
            <li>
              <Code>host_list</Code>, <Code>host_create</Code>
            </li>
            <li>
              <Code>auth_start</Code>, <Code>auth_poll</Code> — device flow, no token required
            </li>
            <li>
              <Code>key_list</Code>, <Code>key_get</Code>, <Code>key_create</Code>, <Code>key_rotate</Code>,{" "}
              <Code>key_update</Code>, <Code>key_delete</Code>, <Code>key_decrypt</Code> — only{" "}
              <Code>key_decrypt</Code> returns a stored value; never echo it into chat
            </li>
            <li>
              <Code>mcp_agent_token_list</Code>, <Code>mcp_agent_token_rotate</Code>,{" "}
              <Code>mcp_agent_token_revoke</Code> — per-agent MCP tokens (WP-02 bot id)
            </li>
          </ul>
          <p className="lb-doc-muted">
            Not on the hosted server today: SQL execution, migrations, storage, functions, billing, and log tools.
          </p>
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
