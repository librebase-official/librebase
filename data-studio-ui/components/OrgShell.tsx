"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

function navClass(pathname: string, href: string): string {
  const active =
    href === "/projects"
      ? pathname === "/projects" || pathname.startsWith("/projects/")
      : pathname === href || pathname.startsWith(`${href}/`);
  return `nav-link${active ? " active" : ""}`;
}

export function OrgShell({
  orgId,
  children,
}: {
  orgId: string;
  children: React.ReactNode;
}) {
  const pathname = usePathname();

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          Libre<span>base</span>
        </div>
        <div className="muted" style={{ fontSize: "0.8rem" }}>
          Org: {orgId}
        </div>

        <nav className="nav-section">
          <div className="nav-label">Primary</div>
          <Link href="/projects" className={navClass(pathname, "/projects")}>
            Projects
          </Link>
          <Link href="/projects/new" className={navClass(pathname, "/projects/new")}>
            New project
          </Link>
        </nav>

        <nav className="nav-section">
          <div className="nav-label">Cloud</div>
          <Link href="/hosts" className={navClass(pathname, "/hosts")}>
            VMs / hosts
          </Link>
          <Link href="/instances" className={navClass(pathname, "/instances")}>
            Instances
          </Link>
          <Link href="/logs" className={navClass(pathname, "/logs")}>
            Logs
          </Link>
        </nav>

        <nav className="nav-section">
          <div className="nav-label">Admin</div>
          <Link href="/admin" className={navClass(pathname, "/admin")}>
            Admin
          </Link>
          <Link href="/login" className={navClass(pathname, "/login")}>
            Login
          </Link>
          <Link href="/setup" className={navClass(pathname, "/setup")}>
            Setup
          </Link>
        </nav>
      </aside>
      <main className="main">{children}</main>
    </div>
  );
}
