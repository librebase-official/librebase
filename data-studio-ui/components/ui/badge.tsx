"use client";

import type { ReactNode } from "react";
import { clsx } from "./clsx";

export type BadgeVariant = "default" | "running" | "stopped" | "starting" | "error" | "warning" | "info" | "success";

export interface BadgeProps {
  children: ReactNode;
  variant?: BadgeVariant;
  className?: string;
}

export function Badge({ children, variant = "default", className }: BadgeProps) {
  const variantClass = {
    default: "badge",
    running: "badge running",
    stopped: "badge stopped",
    starting: "badge starting",
    error: "badge error",
    warning: "badge warning",
    info: "badge info",
    success: "badge success",
  }[variant];
  return <span className={clsx(variantClass, className)}>{children}</span>;
}
