"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Dialog, DialogFooter } from "@/components/ui/dialog";
import { IconTrash } from "@/components/studio/icons";
import { clsx } from "@/components/ui/clsx";

interface DeleteButtonProps {
  href: string;
  confirmTitle: string;
  confirmBody?: string;
  /** Accessible name for the icon button (also the confirm button label). */
  label?: string;
  className?: string;
  /** Where to navigate after successful delete (e.g. "/projects" for project home). */
  redirectTo?: string;
  /** Called after successful delete (before redirect/refresh). Use to drop the card immediately. */
  onSuccess?: () => void;
}

export function DeleteButton({
  href,
  confirmTitle,
  confirmBody,
  label = "Delete",
  className,
  redirectTo,
  onSuccess,
}: DeleteButtonProps) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function confirm() {
    setPending(true);
    setError(null);
    try {
      const res = await fetch(href, { method: "DELETE" });
      const body = (await res.json().catch(() => ({}))) as { error?: string };
      if (!res.ok) {
        setError(body.error ?? "Delete failed");
        return;
      }
      setOpen(false);
      onSuccess?.();
      if (redirectTo) {
        router.push(redirectTo);
      }
      router.refresh();
    } catch {
      setError("Delete request failed");
    } finally {
      setPending(false);
    }
  }

  return (
    <>
      <button
        type="button"
        className={clsx("st-icon-btn delete-icon-btn", className)}
        onClick={(e) => {
          e.preventDefault();
          e.stopPropagation();
          setError(null);
          setOpen(true);
        }}
        aria-label={label}
        title={label}
      >
        <IconTrash width="14" height="14" />
      </button>

      <Dialog
        open={open}
        onClose={() => {
          if (!pending) setOpen(false);
        }}
        title={confirmTitle}
        description={confirmBody}
        size="sm"
      >
        {error ? <p className="auth-error">{error}</p> : null}
        <DialogFooter>
          <button
            type="button"
            className="btn"
            onClick={() => setOpen(false)}
            disabled={pending}
          >
            Cancel
          </button>
          <button
            type="button"
            className="btn btn-destructive"
            onClick={confirm}
            disabled={pending}
          >
            {pending ? "Deleting…" : label}
          </button>
        </DialogFooter>
      </Dialog>
    </>
  );
}
