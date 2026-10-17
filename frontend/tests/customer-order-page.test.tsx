import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import { CustomerOrderPage } from "../src/pages/CustomerOrderPage";
import { api } from "../src/lib/api-client";

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("customer order entry", () => {
  it("does not start microphone capture while the backend voice route is unavailable", () => {
    vi.spyOn(api, "products").mockResolvedValue([]);
    render(<MemoryRouter><CustomerOrderPage /></MemoryRouter>);

    expect(screen.getByText("Voice is coming soon")).toBeInTheDocument();
    expect(screen.getByText("Your microphone won’t be activated")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Start my list" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Start voice recording" })).not.toBeInTheDocument();
  });

  it("shows a single catalogue connection error with a retry action", async () => {
    vi.spyOn(api, "products").mockRejectedValue(new Error("Backend is offline."));
    render(<MemoryRouter><CustomerOrderPage /></MemoryRouter>);

    expect(await screen.findByText("Backend is offline.")).toBeInTheDocument();
    expect(screen.getAllByRole("alert")).toHaveLength(1);
    expect(screen.getByRole("button", { name: "Try again" })).toBeInTheDocument();
  });
});
