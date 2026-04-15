/**
 * Tests for leaderboard component utilities.
 */
import { describe, it, expect } from "vitest";
import { formatSteps, tierBadgeHtml } from "../src/components/leaderboard";

describe("formatSteps", () => {
  it("formats numbers with locale separators", () => {
    const result = formatSteps(10000);
    // Result depends on locale, but should contain "10" and "000"
    expect(result).toContain("10");
    expect(result).toContain("000");
  });

  it("handles zero", () => {
    expect(formatSteps(0)).toBe("0");
  });
});

describe("tierBadgeHtml", () => {
  it("returns gold badge HTML", () => {
    const html = tierBadgeHtml("gold");
    expect(html).toContain("badge--gold");
    expect(html).toContain("Gold");
  });

  it("returns silver badge HTML", () => {
    const html = tierBadgeHtml("silver");
    expect(html).toContain("badge--silver");
  });

  it("returns bronze badge HTML", () => {
    const html = tierBadgeHtml("bronze");
    expect(html).toContain("badge--bronze");
  });

  it("returns empty string for none tier", () => {
    expect(tierBadgeHtml("none")).toBe("");
  });
});
