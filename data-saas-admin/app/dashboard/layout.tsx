"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV = [
  { href: "/dashboard", label: "Overview", icon: "◉" },
  { href: "/dashboard/hosts", label: "Hosts", icon: "⬡" },
  { href: "/dashboard/instances", label: "Instances", icon: "◈" },
  { href: "/dashboard/orgs", label: "Organizations", icon: "◫" },
  { href: "/dashboard/users", label: "Users", icon: "☺" },
  { href: "/dashboard/system", label: "System", icon: "⚙" },
];

export default function DashboardLayout({
  children,
}: { children: React.ReactNode }) {
  const pathname = usePathname();
  return (
    <div className="admin-root">
      <nav className="admin-sidebar">
        <div className="admin-brand">
          Libre<span>base</span> Admin
        </div>
        <div className="admin-nav-label">Dashboard</div>
        {NAV.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={`admin-nav-link${pathname === item.href ? " active" : ""}`}
          >
            <span aria-hidden>{item.icon}</span>
            {item.label}
          </Link>
        ))}
      </nav>
      <main className="admin-main">{children}</main>
    </div>
  );
}
