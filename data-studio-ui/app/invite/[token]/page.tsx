import Link from "next/link";
import { Suspense, use } from "react";
import { adminPreviewInvite } from "@/lib/librebase-admin-client";
import { AcceptButton } from "./AcceptButton";

async function InvitePreview({ token }: { token: string }) {
  const invite = await adminPreviewInvite(token).catch(() => null);
  if (!invite) {
    return <p className="muted">This invite link is invalid or no longer available.</p>;
  }
  return (
    <dl className="invite-preview">
      <div>
        <dt className="muted">Organization</dt>
        <dd>{invite.orgName}</dd>
      </div>
      <div>
        <dt className="muted">Email</dt>
        <dd>{invite.email}</dd>
      </div>
      <div>
        <dt className="muted">Role</dt>
        <dd>{invite.role}</dd>
      </div>
      <div>
        <dt className="muted">Expires</dt>
        <dd>{invite.expiresAt}</dd>
      </div>
    </dl>
  );
}

export default function InvitePage({
  params,
}: {
  params: Promise<{ token: string }>;
}) {
  const token = use(params).token;
  return (
    <div className="auth-page">
      <div className="auth-card">
        <h1>Join organization</h1>
        <Suspense fallback={<p className="muted">Loading invite…</p>}>
          <InvitePreview token={token} />
        </Suspense>
        <p className="muted">
          Sign in as the invited email address, then accept below to join the
          organization and switch into it.
        </p>
        <AcceptButton token={token} />
        <p className="muted auth-foot">
          Not signed in? <Link href={`/login?next=/invite/${token}`}>Sign in</Link>
        </p>
      </div>
    </div>
  );
}
