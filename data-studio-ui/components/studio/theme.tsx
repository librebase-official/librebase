"use client";

import { useEffect, useState } from "react";
import { IconMoon, IconSun } from "./icons";

export type StudioTheme = "light" | "dark";

const KEY = "lb-studio-theme";

export function readTheme(): StudioTheme {
  if (typeof window === "undefined") return "light";
  const stored = window.localStorage.getItem(KEY);
  if (stored === "dark" || stored === "light") return stored;
  return window.matchMedia("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
}

export function applyTheme(theme: StudioTheme) {
  document.documentElement.dataset.theme = theme;
  window.localStorage.setItem(KEY, theme);
}

export function ThemeToggle() {
  const [theme, setTheme] = useState<StudioTheme>("light");

  useEffect(() => {
    setTheme(readTheme());
  }, []);

  function toggle() {
    const next = theme === "light" ? "dark" : "light";
    setTheme(next);
    applyTheme(next);
  }

  return (
    <button
      type="button"
      className="st-icon-btn"
      aria-label={theme === "light" ? "Switch to dark theme" : "Switch to light theme"}
      aria-pressed={theme === "dark"}
      onClick={toggle}
    >
      {theme === "dark" ? <IconSun /> : <IconMoon />}
    </button>
  );
}


