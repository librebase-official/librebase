"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import OrgSwitcher from "@/components/OrgSwitcher";
import { CommandPalette, type CommandItem } from "./CommandPalette";
import { ConnectDialog } from "./ConnectDialog";
import {
  IconAuth,
  IconChart,
  IconDatabase,
  IconEdge,
  IconHome,
  IconKey,
  IconLogs,
  IconMark,
  IconRealtime,
  IconSearch,
  IconServer,
  IconSettings,
  IconSql,
  IconStorage,
  IconTable,
  IconTodo,
  IconUser,
} from "./icons";
import { ThemeToggle } from "./theme";

interface ProjectChrome {
  id: string;
  name: string;
}

const ProjectChromeContext = createContext<{
  project: ProjectChrome | null;
  setProject: (p: ProjectChrome | null) => void;
}>({ project: null, setProject: () => {} });

export function useProjectChrome() {
  return useContext(ProjectChromeContext);
}

export function ProjectChromeSetter({
  id,
  name,
}: {
  id: string;
  name: string;
}) {
  const { setProject } = useProjectChrome();
  useEffect(() => {
    setProject({ id, name });
    return () => setProject(null);
  }, [id, name, setProject]);
  return null;
}

function parseProjectId(pathname: string): string | null {
  const m = pathname.match(/^\/projects\/([^/]+)/);
  if (!m || m[1] === "new") return null;
  return m[1];
}

function railActive(pathname: string, href: string, exact = false): boolean {
  if (exact) return pathname === href;
  if (href === "/projects") {
    return pathname === "/projects" || pathname === "/projects/new";
  }
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function StudioProvider({
  orgId,
  children,
}: {
  orgId: string;
  children: ReactNode;
}) {
  const [project, setProject] = useState<ProjectChrome | null>(null);
  const value = useMemo(() => ({ project, setProject }), [project]);
  return (
    <ProjectChromeContext.Provider value={value}>
      <StudioFrame orgId={orgId}>{children}</StudioFrame>
    </ProjectChromeContext.Provider>
  );
}

function StudioFrame({
  orgId,
  children,
}: {
  orgId: string;
  children: ReactNode;
}) {
  const pathname = usePathname();
  const router = useRouter();
  const { project } = useProjectChrome();
  const [cmdOpen, setCmdOpen] = useState(false);
  const [signingOut, setSigningOut] = useState(false);

  const projectId = parseProjectId(pathname);
  const inProject = Boolean(projectId);
  const projectName = project?.name ?? projectId ?? "Project";

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setCmdOpen((v) => !v);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  async function signOut() {
    setSigningOut(true);
    try {
      await fetch("/api/admin/logout", { method: "POST" });
    } catch {
      /* still leave */
    }
    router.push("/login");
    router.refresh();
  }

  const commands: CommandItem[] = inProject && projectId
    ? [
        { id: "home", label: "Project home", href: `/projects/${projectId}`, group: "Project" },
        { id: "db", label: "Table editor", href: `/projects/${projectId}/database`, group: "Database" },
        { id: "sql", label: "SQL editor", href: `/projects/${projectId}/sql`, group: "Database" },
        { id: "pol", label: "Policies", href: `/projects/${projectId}/database/policies`, group: "Database" },
        { id: "auth", label: "Auth users", href: `/projects/${projectId}/auth`, group: "Auth" },
        { id: "prov", label: "Auth providers", href: `/projects/${projectId}/auth/providers`, group: "Auth" },
        { id: "keys", label: "Keys", href: `/projects/${projectId}/keys`, group: "Auth" },
        { id: "stor", label: "Storage", href: `/projects/${projectId}/storage`, group: "Platform" },
        { id: "edge", label: "Edge functions", href: `/projects/${projectId}/functions`, group: "Platform" },
        { id: "rt", label: "Realtime", href: `/projects/${projectId}/realtime`, group: "Platform" },
        { id: "logs", label: "Logs", href: `/logs`, group: "Observability" },
        { id: "set", label: "Project settings", href: `/projects/${projectId}/settings`, group: "Project" },
        { id: "all", label: "All projects", href: "/projects", group: "Org" },
        { id: "hosts", label: "VMs / hosts", href: "/hosts", group: "Org" },
        { id: "inst", label: "Instances", href: "/instances", group: "Org" },
        { id: "logs", label: "Logs", href: "/logs", group: "Org" },
      ]
    : [
        { id: "proj", label: "Projects", href: "/projects", group: "Org" },
        { id: "newp", label: "New project", href: "/projects/new", group: "Org" },
        { id: "hosts", label: "VMs / hosts", href: "/hosts", group: "Cloud" },
        { id: "newh", label: "Rent a VM", href: "/hosts/new", group: "Cloud" },
        { id: "inst", label: "Instances", href: "/instances", group: "Cloud" },
        { id: "newi", label: "New instance", href: "/instances/new", group: "Cloud" },
        { id: "logs", label: "Logs", href: "/logs", group: "Observability" },
        { id: "admin", label: "Admin", href: "/admin", group: "Account" },
      ];

  return (
    <div className="st-root">
      <header className="st-topbar">
        <Link href="/projects" className="st-wordmark" aria-label="Librebase">
          <span className="st-mark">
            <IconMark />
          </span>
          <span className="st-wordmark-text">
            Libre<em>base</em>
          </span>
        </Link>

        <nav className="st-crumbs" aria-label="Breadcrumb">
          <OrgSwitcher orgId={orgId} variant="crumb" />
          {inProject ? (
            <>
              <span className="st-crumb-sep" aria-hidden>
                /
              </span>
              <Link href={`/projects/${projectId}`} className="st-crumb">
                {projectName}
              </Link>
              <span className="st-crumb-badge">local</span>
            </>
          ) : null}
        </nav>

        <div className="st-top-actions">
          {inProject && projectId ? <ConnectDialog projectId={projectId} /> : null}
          <button
            type="button"
            className="st-search"
            onClick={() => setCmdOpen(true)}
          >
            <IconSearch width="14" height="14" />
            <span>Search</span>
            <kbd>⌘K</kbd>
          </button>
          <ThemeToggle />
          <button
            type="button"
            className="st-icon-btn"
            aria-label={signingOut ? "Signing out" : "Sign out"}
            onClick={signOut}
            disabled={signingOut}
          >
            <IconUser />
          </button>
        </div>
      </header>

      <div className="st-body">
        {inProject && projectId ? (
          <ProjectRail projectId={projectId} pathname={pathname} />
        ) : (
          <OrgRail pathname={pathname} />
        )}

        <aside className="st-sidebar">
          {inProject && projectId ? (
            <ProjectSidebar projectId={projectId} projectName={projectName} pathname={pathname} />
          ) : (
            <OrgSidebar pathname={pathname} onSignOut={signOut} signingOut={signingOut} />
          )}
        </aside>

        <main className="st-main">{children}</main>
      </div>

      <CommandPalette
        open={cmdOpen}
        onClose={() => setCmdOpen(false)}
        items={commands}
      />
    </div>
  );
}

function OrgRail({ pathname }: { pathname: string }) {
  return (
    <nav className="st-rail" aria-label="Organization">
      <div className="st-rail-group">
        <Link
          href="/projects"
          className={`st-rail-btn${railActive(pathname, "/projects") ? " active" : ""}`}
          data-tip="Projects"
          aria-current={railActive(pathname, "/projects") ? "page" : undefined}
        >
          <IconHome />
        </Link>
        <Link
          href="/instances"
          className={`st-rail-btn${railActive(pathname, "/instances") ? " active" : ""}`}
          data-tip="Instances"
        >
          <IconDatabase />
        </Link>
        <Link
          href="/hosts"
          className={`st-rail-btn${railActive(pathname, "/hosts") ? " active" : ""}`}
          data-tip="VMs / hosts"
        >
          <IconServer />
        </Link>
      </div>
      <div className="st-rail-gap" />
      <div className="st-rail-group">
        <Link
          href="/logs"
          className={`st-rail-btn${railActive(pathname, "/logs") ? " active" : ""}`}
          data-tip="Logs"
        >
          <IconLogs />
        </Link>
        <Link
          href="/analytics"
          className={`st-rail-btn${railActive(pathname, "/analytics") ? " active" : ""}`}
          data-tip="Analytics"
        >
          <IconChart />
        </Link>
      </div>
      <div className="st-rail-spacer" />
      <Link
        href="/admin"
        className={`st-rail-btn${railActive(pathname, "/admin") ? " active" : ""}`}
        data-tip="Admin"
      >
        <IconSettings />
      </Link>
    </nav>
  );
}

function ProjectRail({
  projectId,
  pathname,
}: {
  projectId: string;
  pathname: string;
}) {
  const base = `/projects/${projectId}`;
  return (
    <nav className="st-rail" aria-label="Project">
      <div className="st-rail-group">
        <Link
          href="/projects"
          className={`st-rail-btn${railActive(pathname, "/projects") ? " active" : ""}`}
          data-tip="Organization"
          aria-label="Organization home"
        >
          <IconHome />
        </Link>
        <Link
          href={base}
          className={`st-rail-btn${pathname === base ? " active" : ""}`}
          data-tip="Project"
          aria-label="Project home"
        >
          <IconMark />
        </Link>
        <Link
          href={`${base}/database`}
          className={`st-rail-btn${pathname.startsWith(`${base}/database`) ? " active" : ""}`}
          data-tip="Table editor"
        >
          <IconTable />
        </Link>
        <Link
          href={`${base}/sql`}
          className={`st-rail-btn${pathname.startsWith(`${base}/sql`) ? " active" : ""}`}
          data-tip="SQL editor"
        >
          <IconSql />
        </Link>
        <Link
          href={`${base}/auth`}
          className={`st-rail-btn${pathname.startsWith(`${base}/auth`) ? " active" : ""}`}
          data-tip="Authentication"
        >
          <IconAuth />
        </Link>
        <Link
          href={`${base}/keys`}
          className={`st-rail-btn${pathname.startsWith(`${base}/keys`) ? " active" : ""}`}
          data-tip="Keys"
        >
          <IconKey />
        </Link>
        <Link
          href={`${base}/storage`}
          className={`st-rail-btn${pathname.startsWith(`${base}/storage`) ? " active" : ""}`}
          data-tip="Storage"
        >
          <IconStorage />
        </Link>
        <Link
          href={`${base}/functions`}
          className={`st-rail-btn${pathname.startsWith(`${base}/functions`) ? " active" : ""}`}
          data-tip="Edge functions"
        >
          <IconEdge />
        </Link>
        <Link
          href={`${base}/realtime`}
          className={`st-rail-btn${pathname.startsWith(`${base}/realtime`) ? " active" : ""}`}
          data-tip="Realtime"
        >
          <IconRealtime />
        </Link>
      </div>
      <div className="st-rail-gap" />
      <div className="st-rail-group">
        <Link
          href="/logs"
          className={`st-rail-btn${pathname.startsWith("/logs") ? " active" : ""}`}
          data-tip="Logs"
        >
          <IconLogs />
        </Link>
      </div>
      <div className="st-rail-spacer" />
      <Link
        href={`${base}/settings`}
        className={`st-rail-btn${pathname.startsWith(`${base}/settings`) ? " active" : ""}`}
        data-tip="Settings"
      >
        <IconSettings />
      </Link>
    </nav>
  );
}

function OrgSidebar({
  pathname,
  onSignOut,
  signingOut,
}: {
  pathname: string;
  onSignOut: () => void;
  signingOut: boolean;
}) {
  return (
    <>
      <div className="st-sidebar-head">
        <h2 className="st-sidebar-title">Organization</h2>
      </div>
      <nav className="st-sidebar-nav">
        <div className="st-nav-group">
          <div className="st-nav-label">Projects</div>
          <SideLink href="/projects" pathname={pathname} exact>
            All projects
          </SideLink>
          <SideLink href="/projects/new" pathname={pathname} exact>
            New project
          </SideLink>
        </div>
        <div className="st-nav-group">
          <div className="st-nav-label">Cloud</div>
          <SideLink href="/hosts" pathname={pathname}>
            VMs / hosts
          </SideLink>
          <SideLink href="/instances" pathname={pathname}>
            Instances
          </SideLink>
        </div>
        <div className="st-nav-group">
          <div className="st-nav-label">Observability</div>
          <SideLink href="/logs" pathname={pathname}>
            Logs
          </SideLink>
        </div>
        <div className="st-nav-group">
          <div className="st-nav-label">Account</div>
          <SideLink href="/admin" pathname={pathname}>
            Admin
          </SideLink>
        </div>
      </nav>
      <div className="st-sidebar-foot">
        <button
          type="button"
          className="btn btn-ghost btn-sm btn-block"
          onClick={onSignOut}
          disabled={signingOut}
        >
          {signingOut ? "Signing out…" : "Sign out"}
        </button>
      </div>
    </>
  );
}

function ProjectSidebar({
  projectId,
  projectName,
  pathname,
}: {
  projectId: string;
  projectName: string;
  pathname: string;
}) {
  const base = `/projects/${projectId}`;
  return (
    <>
      <div className="st-sidebar-head">
        <Link href={base} className="st-sidebar-title" style={{ textDecoration: "none", color: "inherit" }}>
          {projectName}
        </Link>
      </div>
      <nav className="st-sidebar-nav">
        <div className="st-nav-group">
          <SideLink href="/projects" pathname={pathname} exact>
            Organization home
          </SideLink>
          <SideLink href={base} pathname={pathname} exact>
            Project home
          </SideLink>
          <SideLink href={`${base}/agent`} pathname={pathname}>
            Agent
          </SideLink>
          <SideLink href="/analytics" pathname={pathname}>
            Analytics
          </SideLink>
        </div>
        <div className="st-nav-group">
          <div className="st-nav-label">Database</div>
          <SideLink href={`${base}/database`} pathname={pathname} exact>
            Tables
          </SideLink>
          <SideLink href={`${base}/database/policies`} pathname={pathname}>
            Policies
          </SideLink>
          <SideLink href={`${base}/sql`} pathname={pathname}>
            SQL editor
          </SideLink>
        </div>
        <div className="st-nav-group">
          <div className="st-nav-label">Auth</div>
          <SideLink href={`${base}/auth`} pathname={pathname} exact>
            Users
          </SideLink>
          <SideLink href={`${base}/auth/providers`} pathname={pathname}>
            Providers
          </SideLink>
          <SideLink href={`${base}/keys`} pathname={pathname}>
            Keys
          </SideLink>
        </div>
        <div className="st-nav-group">
          <div className="st-nav-label">Platform</div>
          <SideLink href={`${base}/storage`} pathname={pathname}>
            Storage
          </SideLink>
          <SideLink href={`${base}/functions`} pathname={pathname}>
            Edge functions <span className="st-pill">Soon</span>
          </SideLink>
          <SideLink href={`${base}/realtime`} pathname={pathname}>
            Realtime
          </SideLink>
          <SideLink href="/logs" pathname={pathname}>
            Logs
          </SideLink>
        </div>
        <div className="st-nav-group">
          <div className="st-nav-label">Configuration</div>
          <SideLink href={`${base}/settings`} pathname={pathname}>
            Settings
          </SideLink>
        </div>
      </nav>
    </>
  );
}

function SideLink({
  href,
  pathname,
  exact,
  children,
}: {
  href: string;
  pathname: string;
  exact?: boolean;
  children: ReactNode;
}) {
  const active = exact
    ? pathname === href
    : pathname === href || pathname.startsWith(`${href}/`);
  return (
    <Link
      href={href}
      className={`st-nav-link${active ? " active" : ""}`}
      aria-current={active ? "page" : undefined}
    >
      {children}
    </Link>
  );
}
