"use client";

import type { LabelHTMLAttributes, ReactNode } from "react";
import { clsx } from "./clsx";

export interface FormFieldProps {
  label: string;
  htmlFor?: string;
  error?: string;
  hint?: string;
  children: ReactNode;
  className?: string;
}

export function FormField({ label, htmlFor, error, hint, children, className }: FormFieldProps) {
  return (
    <div className={clsx("field", error ? "field-error" : undefined, className)}>
      <label htmlFor={htmlFor ?? label} className="field-label">
        {label}
      </label>
      {children}
      {hint && !error && <p className="field-hint">{hint}</p>}
      {error && <p className="field-error-text">{error}</p>}
    </div>
  );
}

export interface FormLabelProps extends LabelHTMLAttributes<HTMLLabelElement> {}

export function FormLabel({ className, ...props }: FormLabelProps) {
  return <label className={clsx("field-label", className)} {...props} />;
}
