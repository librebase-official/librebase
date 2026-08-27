"use client";

import type { SelectHTMLAttributes } from "react";
import { clsx } from "./clsx";

export interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {}

export function Select({ className, ...props }: SelectProps) {
  return <select className={clsx("select", className)} {...props} />;
}
