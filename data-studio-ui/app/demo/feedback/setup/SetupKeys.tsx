"use client";

import { useState } from "react";
import { OAuthKeysPanel } from "@/app/(studio)/(cloud)/projects/[projectId]/auth/providers/providers-form";
import type { ProjectAuthProvider } from "@/lib/librebase-admin-client";
import { CopyField } from "@/components/CopyField";
import { SITE_URL } from "@/lib/site";
import { FEEDBACK_ORIGIN } from "@/lib/demo";

export function SetupKeys({
  projectId,
  callbackUrl,
  initialProviders,
  wallUrl,
}: {
  projectId: string;
  callbackUrl: string;
  initialProviders: ProjectAuthProvider[];
  wallUrl: string;
}) {
  const [providers, setProviders] = useState(initialProviders);
  const homepage = FEEDBACK_ORIGIN;

  return (
    <div className="auth-page" style={{ alignItems: "flex-start", paddingTop: 48 }}>
      <div className="auth-card" style={{ maxWidth: 640 }}>
        <p className="st-wordmark" style={{ border: 0, padding: 0, height: "auto", marginBottom: 12 }}>
          Libre<em>base</em>
        </p>
        <h1>Paste OAuth keys here</h1>
        <p className="muted">
          Email/password is already on for this project. MCP opened this page so you never
          paste GitHub or Google secrets in chat. Create two <strong>new</strong> apps (not
          the Studio login apps) with the values below, then paste Client ID and secret into
          the cards.
        </p>

        <ol className="fb-setup-steps">
          <li>
            <strong>GitHub</strong> →{" "}
            <a href="https://github.com/settings/developers" target="_blank" rel="noreferrer">
              New OAuth App
            </a>
            <ul>
              <li>Application name: <code>Librebase feedback</code></li>
              <li>Homepage URL: <code>{homepage}</code></li>
              <li>Authorization callback URL: the callback copied below</li>
            </ul>
          </li>
          <li>
            <strong>Google</strong> →{" "}
            <a href="https://console.cloud.google.com/apis/credentials" target="_blank" rel="noreferrer">
              Create OAuth client (Web application)
            </a>
            <ul>
              <li>
                Authorized JavaScript origins: <code>{homepage}</code> and{" "}
                <code>{SITE_URL}</code>
              </li>
              <li>Authorized redirect URI: the same callback (not /login)</li>
            </ul>
          </li>
          <li>Paste Client ID + secret in the cards. App URL after login is prefilled.</li>
          <li>
            Open the <a href={wallUrl}>feedback wall</a> and click Continue with GitHub / Google.
          </li>
        </ol>

        <CopyField label="Homepage URL" value={homepage} />

        <OAuthKeysPanel
          projectId={projectId}
          callbackUrl={callbackUrl}
          providers={providers}
          defaultAppUrl={homepage}
          onSaved={(next) => {
            setProviders((prev) => {
              const rest = prev.filter((p) => p.provider !== next.provider);
              return [...rest, next];
            });
          }}
        />

        <p className="muted auth-foot">
          <a href={wallUrl}>Go to the feedback wall →</a>
        </p>
      </div>
    </div>
  );
}
