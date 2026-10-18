import Link from "next/link";
import { BrandWordmark } from "@/components/brand/BrandWordmark";

export default function NotFound() {
  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="brand-wordmark-wrap">
          <BrandWordmark href="/landing" size="md" />
        </div>
        <p className="notfound-code">404</p>
        <h1>Page not found</h1>
        <p className="muted">
          This page does not exist — or it belongs to a different organization.
          If you followed a link, it may have been renamed or deleted.
        </p>
        <div className="notfound-actions">
          <Link href="/projects" className="btn btn-primary">
            Go to projects
          </Link>
          <Link href="/login" className="btn">
            Sign in
          </Link>
        </div>
      </div>
    </div>
  );
}