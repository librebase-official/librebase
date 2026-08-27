"use client";

import type { ReactNode } from "react";
import { clsx } from "./clsx";

export interface CardProps {
  title?: string;
  subtitle?: ReactNode;
  headerAction?: ReactNode;
  children: ReactNode;
  className?: string;
  onClick?: () => void;
}

export function Card({ title, subtitle, headerAction, children, className, onClick }: CardProps) {
  return (
    <div className={clsx("card", className)} onClick={onClick}>
      {(title || subtitle || headerAction) && (
        <div className="card-header">
          {title && <h2 className="card-title">{title}</h2>}
          {subtitle && <p className="card-subtitle">{subtitle}</p>}
          {headerAction && <div className="card-header-action">{headerAction}</div>}
        </div>
      )}
      {children}
    </div>
  );
}
