import { act, renderHook } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { useRecorder } from "../src/hooks/use-recorder";

describe("browser voice recording", () => {
  it("reports unsupported microphone capture and keeps the text-order fallback available", async () => {
    const { result } = renderHook(() => useRecorder(async () => {}));

    await act(async () => {
      await result.current.start();
    });

    expect(result.current.state).toBe("unsupported");
    expect(result.current.error).toContain("type your order instead");
  });
});
