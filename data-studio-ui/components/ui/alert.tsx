"use client";

import type { ReactNode } from "react";
import { clsx } from "./clsx";

export type AlertVariant = "warn" | "error" | "info" | "success";

export interface AlertProps {
  children: ReactNode;
  variant?: AlertVariant;
  className?: string;
}

export function Alert({ children, variant = "info", className }: AlertProps) {
  return (
    <div className={clsx("alert", `alert-${variant}`, className)}>
      {children}
    </div>
  );
}
