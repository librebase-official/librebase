"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState } from "react";
import OrgSwitcher from "@/components/OrgSwitcher";

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
  const router = useRouter();
  const [signingOut, setSigningOut] = useState(false);

  async function signOut() {
    setSigningOut(true);
    try {
      await fetch("/api/admin/logout", { method: "POST" });
    } catch {
      // ignore network errors — still clear the local session below
    }
    router.push("/login");
    router.refresh();
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          Libre<span>base</span>
        </div>
        <div className="muted" style={{ fontSize: "0.8rem", marginBottom: "0.5rem" }}>
          <OrgSwitcher orgId={orgId} />
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
          <div className="nav-label">Account</div>
          <Link href="/admin" className={navClass(pathname, "/admin")}>
            Settings
          </Link>
        </nav>

        <nav className="nav-section">
          <div className="nav-label">Advanced</div>
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

        <div className="sidebar-spacer" />
        <button
          type="button"
          className="btn btn-ghost sign-out"
          onClick={signOut}
          disabled={signingOut}
        >
          {signingOut ? "Signing out…" : "Sign out"}
        </button>
      </aside>
      <main className="main">{children}</main>
    </div>
  );
}
