"use client";

import type { ButtonHTMLAttributes } from "react";
import { clsx } from "./clsx";

export type ButtonVariant =
  | "primary"
  | "secondary"
  | "ghost"
  | "destructive"
  | "primary-outline";

export type ButtonSize = "sm" | "md" | "lg";

export interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
}

export function Button({
  variant = "secondary",
  size = "md",
  className,
  disabled,
  ...props
}: ButtonProps) {
  const variantClass = {
    primary: "btn btn-primary",
    secondary: "btn",
    ghost: "btn btn-ghost",
    destructive: "btn btn-destructive",
    "primary-outline": "btn btn-primary-outline",
  }[variant];
  const sizeClass = {
    sm: "btn-sm",
    md: "",
    lg: "btn-lg",
  }[size];
  return (
    <button
      className={clsx(variantClass, sizeClass, className)}
      disabled={disabled}
      {...props}
    />
  );
}
