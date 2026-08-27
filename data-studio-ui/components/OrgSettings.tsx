"use client";

import { useState, useTransition } from "react";
import { adminUpdateOrg } from "@/lib/librebase-admin-client";
import { Button, Dialog, DialogFooter, Input } from "@/components/ui";

export interface OrgSettingsProps {
  orgId: string;
  currentName: string;
  role: "owner" | "admin" | "developer";
  className?: string;
}

export function OrgSettings({ orgId, currentName, role }: OrgSettingsProps) {
  const [open, setOpen] = useState(false);
  const [name, setName] = useState(currentName);
  const [saving, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);
  const [savedName, setSavedName] = useState(currentName);

  const canEdit = role === "owner" || role === "admin";

  const openDialog = () => {
    setName(currentName);
    setError(null);
    setOpen(true);
  };

  const save = () => {
    const trimmed = name.trim();
    if (!trimmed || trimmed === savedName) {
      setOpen(false);
      return;
    }
    startTransition(async () => {
      setError(null);
      try {
        await adminUpdateOrg(orgId, { name: trimmed });
        setSavedName(trimmed);
        setOpen(false);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to update org name");
      }
    });
  };

  return (
    <>
      <Button
        variant="ghost"
        size="sm"
        onClick={openDialog}
        disabled={!canEdit}
        aria-label={canEdit ? "Edit organization name" : undefined}
      >
        {canEdit ? "Edit name" : "View name"}
      </Button>

      <Dialog
        open={open}
        onClose={() => {
          if (!saving) {
            setName(savedName);
            setError(null);
            setOpen(false);
          }
        }}
        title="Edit organization name"
        description="This name is shown in the org switcher and admin panel."
      >
        <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          <Input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Acme Inc."
            autoFocus
            disabled={saving}
            style={{ maxWidth: "100%" }}
          />
          {error ? <p className="auth-error">{error}</p> : null}
        </div>
        <DialogFooter>
          <Button
            variant="ghost"
            size="sm"
            disabled={saving}
            onClick={() => {
              setName(savedName);
              setError(null);
              setOpen(false);
            }}
          >
            Cancel
          </Button>
          <Button
            variant="primary"
            size="sm"
            disabled={saving || !name.trim() || name.trim() === savedName}
            onClick={save}
          >
            {saving ? "Saving…" : "Save"}
          </Button>
        </DialogFooter>
      </Dialog>
    </>
  );
}
