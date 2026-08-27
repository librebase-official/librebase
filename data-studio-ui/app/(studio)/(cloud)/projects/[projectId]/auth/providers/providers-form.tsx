"use client";

import { useEffect, useMemo, useState, useTransition } from "react";
import { Toggle } from "@/components/studio/Toggle";
import { CopyField } from "@/components/CopyField";
import { Button } from "@/components/ui";
import type { AuthSettings } from "@/lib/auth-settings-store";
import type { ProjectAuthProvider } from "@/lib/librebase-admin-client";

const OAUTH = [
  {
    provider: "github" as const,
    title: "GitHub",
    docs: "https://github.com/settings/developers",
    help: "Create an OAuth App. Authorization callback URL must match the callback below.",
  },
  {
    provider: "google" as const,
    title: "Google",
    docs: "https://console.cloud.google.com/apis/credentials",
    help: "Create a Web application OAuth client. Authorized redirect URI must match the callback below.",
  },
];

export function ProvidersForm({
  projectId,
  callbackUrl,
  initialProviders = [],
}: {
  projectId: string;
  callbackUrl: string;
  initialProviders?: ProjectAuthProvider[];
}) {
  const [settings, setSettings] = useState<AuthSettings | null>(null);
  const [savingFlags, setSavingFlags] = useState(false);
  const [providers, setProviders] = useState<ProjectAuthProvider[]>(initialProviders);

  useEffect(() => {
    fetch(`/api/projects/${projectId}/auth/settings`)
      .then((r) => r.json())
      .then((body: { settings?: AuthSettings }) => setSettings(body.settings ?? null));
  }, [projectId]);

  async function patch(next: Partial<AuthSettings>) {
    if (!settings) return;
    const optimistic = { ...settings, ...next };
    setSettings(optimistic);
    setSavingFlags(true);
    try {
      const res = await fetch(`/api/projects/${projectId}/auth/settings`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(next),
      });
      const body = (await res.json()) as { settings?: AuthSettings };
      if (body.settings) setSettings(body.settings);
    } finally {
      setSavingFlags(false);
    }
  }

  if (!settings) return <p className="muted">Loading…</p>;

  const rows: { key: keyof AuthSettings; title: string; help: string }[] = [
    { key: "allowSignup", title: "Allow new users to sign up", help: "If this is off, the auth API rejects registrations." },
    { key: "confirmEmail", title: "Confirm email", help: "Users confirm their address before the first session." },
    { key: "allowAnonymous", title: "Allow anonymous sign-ins", help: "Issue anonymous sessions for this project." },
    { key: "allowManualLinking", title: "Allow manual linking", help: "Enable manual linking APIs for your project." },
    { key: "emailProvider", title: "Email / password", help: "Librebase Auth email provider." },
  ];

  return (
    <div className="st-settings">
      <h2 className="section-title">User signups</h2>
      <div className="st-panel">
        {rows.map((row) => (
          <div className="st-row" key={row.key}>
            <div className="st-row-copy">
              <strong>{row.title}</strong>
              <p>{row.help}</p>
            </div>
            <Toggle
              label={row.title}
              checked={Boolean(settings[row.key])}
              onChange={(v) => void patch({ [row.key]: v })}
            />
          </div>
        ))}
      </div>
      {savingFlags ? <p className="muted text-sm mt-2">Saving…</p> : null}

      <OAuthKeysPanel
        projectId={projectId}
        callbackUrl={callbackUrl}
        providers={providers}
        onSaved={(next) => {
          setProviders((prev) => {
            const rest = prev.filter((p) => p.provider !== next.provider);
            return [...rest, next];
          });
        }}
      />
    </div>
  );
}

export function OAuthKeysPanel({
  projectId,
  callbackUrl,
  providers,
  onSaved,
  defaultAppUrl = "",
}: {
  projectId: string;
  callbackUrl: string;
  providers: ProjectAuthProvider[];
  onSaved: (provider: ProjectAuthProvider) => void;
  defaultAppUrl?: string;
}) {
  return (
    <>
      <h2 className="section-title" style={{ marginTop: 8 }}>
        Paste GitHub & Google keys
      </h2>
      <p className="muted text-sm" style={{ marginBottom: 12 }}>
        These credentials sign in <em>your app’s users</em>, not Studio operators. Paste them
        here — never in chat. Register the callback URL on both providers first.
      </p>
      <CopyField label="Callback URL (paste this in GitHub and Google)" value={callbackUrl} />
      {OAUTH.map((spec) => (
        <OAuthAppCard
          key={spec.provider}
          spec={spec}
          projectId={projectId}
          callbackUrl={callbackUrl}
          defaultAppUrl={defaultAppUrl}
          current={providers.find((p) => p.provider === spec.provider)}
          onSaved={onSaved}
        />
      ))}
    </>
  );
}

function OAuthAppCard({
  spec,
  projectId,
  callbackUrl,
  current,
  onSaved,
  defaultAppUrl = "",
}: {
  spec: (typeof OAUTH)[number];
  projectId: string;
  callbackUrl: string;
  current?: ProjectAuthProvider;
  onSaved: (provider: ProjectAuthProvider) => void;
  defaultAppUrl?: string;
}) {
  const [clientId, setClientId] = useState(current?.clientId ?? "");
  const [clientSecret, setClientSecret] = useState("");
  const [appUrl, setAppUrl] = useState(
    current?.redirectUris?.filter((u) => u !== callbackUrl)[0] ?? defaultAppUrl,
  );
  const [enabled, setEnabled] = useState(current?.enabled ?? true);
  const [error, setError] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();
  const startUrl = useMemo(() => {
    const dest = appUrl.trim() || callbackUrl;
    return `/api/projects/${projectId}/auth/oauth/start?provider=${spec.provider}&redirect_to=${encodeURIComponent(dest)}`;
  }, [appUrl, callbackUrl, projectId, spec.provider]);

  function save() {
    startTransition(async () => {
      setError(null);
      const redirectUris = [callbackUrl];
      if (appUrl.trim()) redirectUris.push(appUrl.trim());
      const res = await fetch(`/api/projects/${projectId}/auth/providers`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          provider: spec.provider,
          clientId: clientId.trim(),
          clientSecret: clientSecret.trim() || undefined,
          redirectUris,
          enabled,
        }),
      });
      const body = (await res.json().catch(() => ({}))) as {
        provider?: ProjectAuthProvider;
        error?: string;
      };
      if (!res.ok || !body.provider) {
        setError(body.error ?? `Save failed (${res.status})`);
        return;
      }
      setClientSecret("");
      onSaved(body.provider);
    });
  }

  return (
    <section className="st-panel" style={{ marginTop: 16 }}>
      <div className="st-row">
        <div className="st-row-copy">
          <strong>{spec.title}</strong>
          <p>
            {spec.help}{" "}
            <a href={spec.docs} target="_blank" rel="noreferrer">
              Open console
            </a>
          </p>
        </div>
        <Toggle
          label={`Enable ${spec.title}`}
          checked={enabled}
          onChange={setEnabled}
        />
      </div>
      <div className="form" style={{ padding: "12px 16px 16px" }}>
        <div className="field">
          <label htmlFor={`${spec.provider}-cid`}>Client ID</label>
          <input
            id={`${spec.provider}-cid`}
            value={clientId}
            onChange={(e) => setClientId(e.target.value)}
            autoComplete="off"
            required
          />
        </div>
        <div className="field">
          <label htmlFor={`${spec.provider}-secret`}>
            Client secret{current ? " (leave blank to keep current)" : ""}
          </label>
          <input
            id={`${spec.provider}-secret`}
            type="password"
            value={clientSecret}
            onChange={(e) => setClientSecret(e.target.value)}
            autoComplete="new-password"
            placeholder={current ? "••••••••" : ""}
          />
        </div>
        <div className="field">
          <label htmlFor={`${spec.provider}-app`}>App URL after login</label>
          <input
            id={`${spec.provider}-app`}
            type="url"
            value={appUrl}
            onChange={(e) => setAppUrl(e.target.value)}
            placeholder="https://your-app.example"
          />
          <p className="muted text-sm">
            GitHub/Google send the user here after Librebase issues a session. Must be HTTPS
            (or localhost).
          </p>
        </div>
        {error ? <p className="auth-error">{error}</p> : null}
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <Button variant="primary" size="sm" onClick={save} disabled={pending || !clientId.trim()}>
            {pending ? "Saving…" : current ? "Update" : "Save"}
          </Button>
          {current?.enabled ? (
            <a className="btn btn-sm" href={startUrl}>
              Test {spec.title} login
            </a>
          ) : null}
        </div>
        {current ? (
          <p className="muted text-sm" style={{ marginTop: 8 }}>
            Configured{current.updatedAt ? ` · ${current.updatedAt}` : ""}. Secret stays in KMS
            and is never shown again.
          </p>
        ) : null}
      </div>
    </section>
  );
}
