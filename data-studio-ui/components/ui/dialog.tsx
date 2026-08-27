"use client";

import type { ReactNode, HTMLAttributes } from "react";
import { useEffect, useRef } from "react";
import { clsx } from "./clsx";
import { createPortal } from "react-dom";

export interface DialogProps {
  open: boolean;
  onClose: () => void;
  title: string;
  description?: string;
  children: ReactNode;
  size?: "sm" | "md" | "lg" | "xl";
}

export function Dialog({ open, onClose, title, description, children, size = "md" }: DialogProps) {
  const overlayRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const onCloseRef = useRef(onClose);
  useEffect(() => {
    onCloseRef.current = onClose;
  }, [onClose]);

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onCloseRef.current();
    };
    if (open) {
      document.addEventListener("keydown", onKeyDown);
      const previously = document.activeElement as HTMLElement | null;
      // Only auto-focus the panel if nothing inside it is already focused
      // (e.g. user is typing in an input). Previously this stole focus on
      // every parent re-render because onClose was recreated each render.
      const active = document.activeElement as HTMLElement | null;
      const panel = panelRef.current;
      const shouldFocusPanel = !active || !panel?.contains(active);
      if (shouldFocusPanel) panel?.focus();
      return () => {
        document.removeEventListener("keydown", onKeyDown);
        // Only restore focus if the active element is still inside the dialog
        // (prevents stealing focus from inputs the user is typing in)
        if (previously && document.contains(previously) && !panel?.contains(document.activeElement)) {
          previously.focus();
        }
      };
    }
  }, [open]);

  useEffect(() => {
    if (open) {
      document.body.style.overflow = "fixed";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [open]);

  const onOverlayClick = (e: React.MouseEvent) => {
    if (e.target === overlayRef.current) onClose();
  };

  if (!open) return null;

  return createPortal(
    <div
      className="dialog-overlay"
      ref={overlayRef}
      onMouseDown={onOverlayClick}
      aria-modal="true"
      role="dialog"
    >
      <div
        className={clsx("dialog-panel", `dialog-panel-${size}`)}
        ref={panelRef}
        tabIndex={-1}
        aria-label={title}
      >
        <div className="dialog-header">
          <h2 className="dialog-title">{title}</h2>
          {description ? <p className="dialog-description">{description}</p> : null}
        </div>
        <div className="dialog-body">{children}</div>
      </div>
    </div>,
    document.body,
  );
}

export interface DialogFooterProps extends HTMLAttributes<HTMLDivElement> {}

export function DialogFooter({ className, ...props }: DialogFooterProps) {
  return <div className={clsx("dialog-footer", className)} {...props} />;
}
