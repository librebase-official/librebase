"use client";

import type { InputHTMLAttributes } from "react";
import { clsx } from "./clsx";

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {}

export function Input({ className, ...props }: InputProps) {
  return <input className={clsx("input", className)} {...props} />;
}
