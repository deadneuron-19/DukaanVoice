import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { useTheme } from "../src/hooks/use-theme";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  localStorage.clear();
  document.documentElement.dataset.theme = "light";
});

function ThemeControl({ label }: { label: string }) {
  const { resolvedTheme, setTheme } = useTheme();
  return (
    <div>
      <span>{label}: {resolvedTheme}</span>
      <button onClick={() => setTheme("dark")}>Use dark mode</button>
    </div>
  );
}

describe("shared theme preference", () => {
  it("updates all mounted controls and the document theme together", () => {
    const media = {
      matches: false,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    };
    vi.stubGlobal("matchMedia", vi.fn(() => media));
    render(
      <>
        <ThemeControl label="Header" />
        <ThemeControl label="Settings" />
      </>,
    );

    fireEvent.click(screen.getAllByRole("button", { name: "Use dark mode" })[0]);

    expect(screen.getByText("Header: dark")).toBeInTheDocument();
    expect(screen.getByText("Settings: dark")).toBeInTheDocument();
    expect(document.documentElement.dataset.theme).toBe("dark");
    expect(localStorage.getItem("dukaanvoice-theme")).toBe("dark");
  });
});
