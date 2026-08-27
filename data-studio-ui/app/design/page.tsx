import Link from "next/link";
import { EmptyState } from "@/components/studio/EmptyState";
import { PageHeader } from "@/components/studio/PageHeader";
import { ThemeToggle } from "@/components/studio/theme";
import {
  IconDatabase,
  IconHome,
  IconLogs,
  IconMark,
  IconPlus,
  IconServer,
  IconSettings,
  IconSql,
  IconTable,
} from "@/components/studio/icons";

export const metadata = {
  title: "Studio design system",
};

function RailMock({ active }: { active: string }) {
  const items = [
    { id: "home", icon: <IconHome />, tip: "Home" },
    { id: "table", icon: <IconTable />, tip: "Tables" },
    { id: "sql", icon: <IconSql />, tip: "SQL" },
    { id: "db", icon: <IconDatabase />, tip: "Instances" },
    { id: "host", icon: <IconServer />, tip: "Hosts" },
    { id: "logs", icon: <IconLogs />, tip: "Logs" },
    { id: "set", icon: <IconSettings />, tip: "Settings" },
  ];
  return (
    <nav className="st-rail" aria-label="Preview rail">
      {items.map((it) => (
        <span
          key={it.id}
          className={`st-rail-btn${it.id === active ? " active" : ""}`}
          data-tip={it.tip}
        >
          {it.icon}
        </span>
      ))}
    </nav>
  );
}

export default function DesignPage() {
  return (
    <div className="st-root">
      <header className="st-topbar">
        <Link href="/design" className="st-wordmark">
          <span className="st-mark">
            <IconMark />
          </span>
          Libre<em>base</em>
        </Link>
        <nav className="st-crumbs">
          <span className="st-crumb">Julian Projects</span>
          <span className="st-crumb-sep">/</span>
          <span className="st-crumb">majico</span>
          <span className="st-crumb-badge">local</span>
        </nav>
        <div className="st-top-actions">
          <button type="button" className="btn btn-ghost btn-sm">
            Connect
          </button>
          <span className="st-search">
            Search <kbd>⌘K</kbd>
          </span>
          <ThemeToggle />
        </div>
      </header>

      <div className="st-body">
        <RailMock active="home" />
        <aside className="st-sidebar">
          <div className="st-sidebar-head">
            <h2 className="st-sidebar-title">majico</h2>
          </div>
          <nav className="st-sidebar-nav">
            <div className="st-nav-group">
              <span className="st-nav-link active">Home</span>
            </div>
            <div className="st-nav-group">
              <div className="st-nav-label">Develop</div>
              <span className="st-nav-link">Table editor</span>
              <span className="st-nav-link">
                SQL editor <span className="st-pill new">New</span>
              </span>
            </div>
            <div className="st-nav-group">
              <div className="st-nav-label">Configuration</div>
              <span className="st-nav-link">
                Settings <span className="st-pill beta">Beta</span>
              </span>
            </div>
          </nav>
        </aside>

        <main className="st-main">
          <PageHeader
            title="Studio design system"
            description="Librebase chrome — Supabase’s workbench principles, our forest-teal identity. Tokens live in docs/brand/STUDIO.md."
            actions={
              <Link href="/projects" className="btn btn-primary">
                Open console
              </Link>
            }
          />

          <nav className="st-tabs">
            <span className="st-tab active">Overview</span>
            <span className="st-tab">Components</span>
            <span className="st-tab">Tokens</span>
          </nav>

          <h2 className="section-title">Color</h2>
          <div className="card-grid" style={{ marginBottom: 32 }}>
            {[
              ["bg", "Canvas"],
              ["surface", "Surface"],
              ["surface-muted", "Muted"],
              ["accent", "Accent"],
              ["signal", "Signal"],
              ["text", "Ink"],
            ].map(([token, label]) => (
              <div key={token} className="card">
                <div
                  style={{
                    height: 56,
                    borderRadius: 6,
                    marginBottom: 10,
                    background: `var(--${token})`,
                    border: "1px solid var(--border)",
                  }}
                />
                <strong>{label}</strong>
                <p className="muted text-sm">{token}</p>
              </div>
            ))}
          </div>

          <h2 className="section-title">Buttons</h2>
          <div className="action-row" style={{ marginBottom: 32 }}>
            <button type="button" className="btn btn-primary">
              <IconPlus width="14" height="14" /> New project
            </button>
            <button type="button" className="btn">
              Secondary
            </button>
            <button type="button" className="btn btn-ghost">
              Ghost
            </button>
            <button type="button" className="btn btn-primary-outline">
              Outline
            </button>
            <button type="button" className="btn btn-danger">
              Destructive
            </button>
          </div>

          <h2 className="section-title">Settings rows</h2>
          <div className="st-settings" style={{ marginBottom: 32 }}>
            <div className="st-panel">
              <div className="st-row">
                <div className="st-row-copy">
                  <strong>Allow new users to sign up</strong>
                  <p>If this is off, the auth API rejects registrations.</p>
                </div>
                <span className="badge running">on</span>
              </div>
              <div className="st-row">
                <div className="st-row-copy">
                  <strong>Confirm email</strong>
                  <p>Users confirm their address before the first session.</p>
                </div>
                <span className="badge">off</span>
              </div>
              <div className="st-row">
                <div className="st-row-copy">
                  <strong>Honest health</strong>
                  <p>Status is a probe. We do not paint this green.</p>
                </div>
                <span className="badge starting">degraded</span>
              </div>
            </div>
          </div>

          <h2 className="section-title">Paused project</h2>
          <EmptyState
            title={'Project “majico” is paused'}
            facts={[
              "All data, including backups, remains on disk.",
              "Resume from this dashboard when you need the API.",
              "Health stays muted until a probe succeeds.",
            ]}
            actions={
              <>
                <button type="button" className="btn">
                  Download backups
                </button>
                <button type="button" className="btn btn-primary">
                  Start project
                </button>
              </>
            }
          />

          <h2 className="section-title">Type</h2>
          <div className="st-panel" style={{ padding: 20 }}>
            <p style={{ fontFamily: "var(--font-display)", fontWeight: 700, margin: "0 0 8px" }}>
              Libre<span style={{ color: "var(--accent)" }}>base</span> — Orbitron wordmark only
            </p>
            <h1 style={{ margin: "0 0 8px" }}>Page title 28 / 600</h1>
            <p className="muted" style={{ margin: "0 0 12px" }}>
              Subtitle in secondary text. One sentence of purpose.
            </p>
            <p className="mono text-sm" style={{ margin: 0 }}>
              ibm plex mono — connection strings and ids
            </p>
          </div>
        </main>
      </div>
    </div>
  );
}
