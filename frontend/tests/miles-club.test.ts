/**
 * Tests for miles club component.
 */
import { describe, it, expect } from "vitest";
import {
  calculateTier,
  renderMilesClubBadge,
  renderTierProgress,
} from "../src/components/miles-club";

describe("calculateTier", () => {
  it("returns high for 10k+ avg daily steps", () => {
    expect(calculateTier(10_000)).toBe("high");
    expect(calculateTier(15_000)).toBe("high");
  });

  it("returns mid for 5k-9999 avg daily steps", () => {
    expect(calculateTier(5_000)).toBe("mid");
    expect(calculateTier(9_999)).toBe("mid");
  });

  it("returns low for under 5k avg daily steps", () => {
    expect(calculateTier(0)).toBe("low");
    expect(calculateTier(4_999)).toBe("low");
  });

  it("uses custom thresholds", () => {
    const custom = { high: 100, mid: 50 };
    expect(calculateTier(100, custom)).toBe("high");
    expect(calculateTier(50, custom)).toBe("mid");
    expect(calculateTier(10, custom)).toBe("low");
  });
});

describe("renderMilesClubBadge", () => {
  it("renders high badge", () => {
    const html = renderMilesClubBadge("high");
    expect(html).toContain(">10k steps/day");
    expect(html).toContain("badge--high");
  });

  it("renders mid badge", () => {
    const html = renderMilesClubBadge("mid");
    expect(html).toContain("steps/day");
    expect(html).toContain("badge--mid");
  });

  it("renders low badge", () => {
    const html = renderMilesClubBadge("low");
    expect(html).toContain("steps/day");
    expect(html).toContain("badge--low");
  });

  it("returns empty string for none", () => {
    expect(renderMilesClubBadge("none")).toBe("");
  });
});

describe("renderTierProgress", () => {
  it("shows progress toward mid for low-tier users", () => {
    const html = renderTierProgress(2_500);
    expect(html).toContain("5k");
    expect(html).toContain("2,500");
  });

  it("shows max for high-tier users", () => {
    const html = renderTierProgress(10_000);
    expect(html).toContain("highest tier");
  });
});
