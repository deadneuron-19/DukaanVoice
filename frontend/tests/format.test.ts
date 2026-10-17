import { describe, expect, it } from "vitest";
import { formatMoney, packLabel } from "../src/lib/format";

describe("display formatting", () => {
  it("formats rupee amounts using Indian locale", () => {
    expect(formatMoney("245.00")).toContain("245");
    expect(formatMoney("245.00")).toContain("₹");
  });

  it("formats package quantities from API data", () => {
    expect(packLabel(5, "kg")).toBe("5 kg");
  });
});
