import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { api } from "../lib/api";

type Theme = "light" | "dark" | "system";

type ThemeContextValue = {
  theme: Theme;
  resolved: "light" | "dark";
  setTheme: (t: Theme) => void;
  themeError: string | null;
};

const ThemeContext = createContext<ThemeContextValue | null>(null);

const STORAGE_KEY = "roleradar-theme";

function readStoredTheme(): Theme {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored === "light" || stored === "dark" || stored === "system") return stored;
  return "system";
}

function resolveTheme(theme: Theme): "light" | "dark" {
  if (theme === "system") {
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }
  return theme;
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = useState<Theme>(readStoredTheme);
  const [themeError, setThemeError] = useState<string | null>(null);
  const resolved = useMemo(() => resolveTheme(theme), [theme]);

  useEffect(() => {
    api
      .getSettings()
      .then((s) => {
        const t = s.theme as Theme;
        if (t === "light" || t === "dark" || t === "system") {
          setThemeState(t);
        }
      })
      .catch(() => {
        /* keep localStorage theme */
      });
  }, []);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", resolved);
    localStorage.setItem(STORAGE_KEY, theme);
  }, [resolved, theme]);

  useEffect(() => {
    if (theme !== "system") return;
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const fn = () => document.documentElement.setAttribute("data-theme", resolveTheme("system"));
    mq.addEventListener("change", fn);
    return () => mq.removeEventListener("change", fn);
  }, [theme]);

  const setTheme = useCallback((t: Theme) => {
    setThemeState(t);
    setThemeError(null);
    api.patchSettings({ theme: t }).catch((e) => {
      setThemeError(e instanceof Error ? e.message : "Could not save theme");
    });
  }, []);

  return (
    <ThemeContext.Provider value={{ theme, resolved, setTheme, themeError }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error("useTheme must be used within ThemeProvider");
  return ctx;
}
