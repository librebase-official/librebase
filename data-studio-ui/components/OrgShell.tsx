"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

function navClass(pathname: string, href: string): string {
  const active =
    href === "/"
      ? pathname === "/"
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
          <Link href="/" className={navClass(pathname, "/")}>
            Projects
          </Link>
          <Link href="/projects/new" className={navClass(pathname, "/projects/new")}>
            New project
          </Link>
        </nav>

        <nav className="nav-section">
          <div className="nav-label">Cloud</div>
          <Link href="/instances" className={navClass(pathname, "/instances")}>
            Instances
          </Link>
        </nav>
      </aside>
      <main className="main">{children}</main>
    </div>
  );
}
