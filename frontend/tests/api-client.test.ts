import { afterEach, describe, expect, it, vi } from "vitest";
import { api } from "../src/lib/api-client";

afterEach(() => vi.unstubAllGlobals());

describe("typed API client", () => {
  it("uses the documented products endpoint", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify([]), { status: 200, headers: { "Content-Type": "application/json" } }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await expect(api.products()).resolves.toEqual([]);
    expect(fetchMock.mock.calls[0][0]).toContain("/products");
  });

  it("normalizes safe API errors and correlation IDs", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ detail: "Stock changed." }), {
        status: 409,
        headers: { "Content-Type": "application/json", "X-Correlation-ID": "req-123" },
      }),
    ));

    await expect(api.health()).rejects.toEqual(expect.objectContaining({
      name: "ApiError",
      status: 409,
      detail: "Stock changed. (Request req-123)",
    }));
  });

  it("explains how to start the backend when the connection is refused", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));

    await expect(api.health()).rejects.toEqual(expect.objectContaining({
      name: "ApiError",
      status: 0,
      detail: expect.stringContaining("Start the backend with the “Start DukaanVoice” task"),
    }));
  });
});
