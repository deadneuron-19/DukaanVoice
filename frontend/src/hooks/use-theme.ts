import { useSyncExternalStore } from "react";

export type ThemeChoice = "light" | "dark" | "system";

const storageKey = "dukaanvoice-theme";
const subscribers = new Set<() => void>();
let theme = readStoredTheme();
let listenersAttached = false;

function parseTheme(value: string | null): ThemeChoice {
  return value === "light" || value === "dark" ? value : "system";
}

function readStoredTheme(): ThemeChoice {
  return parseTheme(localStorage.getItem(storageKey));
}

function getResolvedTheme(): "light" | "dark" {
  return theme === "system"
    ? window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"
    : theme;
}

function applyTheme() {
  const resolved = getResolvedTheme();
  document.documentElement.dataset.theme = resolved;
  document.querySelector('meta[name="theme-color"]')?.setAttribute(
    "content",
    resolved === "dark" ? "#151b17" : "#f7f3e9",
  );
}

function notifySubscribers() {
  subscribers.forEach((subscriber) => subscriber());
}

function handleStorage(event: StorageEvent) {
  if (event.key !== storageKey) return;
  theme = parseTheme(event.newValue);
  applyTheme();
  notifySubscribers();
}

function handleSystemThemeChange() {
  if (theme === "system") {
    applyTheme();
    notifySubscribers();
  }
}

function subscribe(subscriber: () => void) {
  subscribers.add(subscriber);
  if (!listenersAttached) {
    window.addEventListener("storage", handleStorage);
    window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", handleSystemThemeChange);
    listenersAttached = true;
    applyTheme();
  }
  return () => {
    subscribers.delete(subscriber);
    if (subscribers.size === 0 && listenersAttached) {
      window.removeEventListener("storage", handleStorage);
      window.matchMedia("(prefers-color-scheme: dark)").removeEventListener("change", handleSystemThemeChange);
      listenersAttached = false;
    }
  };
}

function setTheme(themeChoice: ThemeChoice) {
  theme = themeChoice;
  localStorage.setItem(storageKey, themeChoice);
  applyTheme();
  notifySubscribers();
}

export function useTheme() {
  const selectedTheme = useSyncExternalStore(subscribe, () => theme, () => "system");
  const resolvedTheme = getResolvedTheme();
  return { theme: selectedTheme, resolvedTheme, setTheme };
}
