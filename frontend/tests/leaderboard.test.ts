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
  it("returns high badge HTML", () => {
    const html = tierBadgeHtml("high");
    expect(html).toContain("badge--high");
    expect(html).toContain(">10k steps/day");
  });

  it("returns mid badge HTML", () => {
    const html = tierBadgeHtml("mid");
    expect(html).toContain("badge--mid");
  });

  it("returns low badge HTML", () => {
    const html = tierBadgeHtml("low");
    expect(html).toContain("badge--low");
  });

  it("returns empty string for none tier", () => {
    expect(tierBadgeHtml("none")).toBe("");
  });
});
