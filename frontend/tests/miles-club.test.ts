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
  it("returns gold for 300k+ steps", () => {
    expect(calculateTier(300_000)).toBe("gold");
    expect(calculateTier(400_000)).toBe("gold");
  });

  it("returns silver for 200k-299k steps", () => {
    expect(calculateTier(200_000)).toBe("silver");
    expect(calculateTier(299_999)).toBe("silver");
  });

  it("returns bronze for 100k-199k steps", () => {
    expect(calculateTier(100_000)).toBe("bronze");
    expect(calculateTier(199_999)).toBe("bronze");
  });

  it("returns none for under 100k steps", () => {
    expect(calculateTier(0)).toBe("none");
    expect(calculateTier(99_999)).toBe("none");
  });

  it("uses custom thresholds", () => {
    const custom = { gold: 100, silver: 50, bronze: 10 };
    expect(calculateTier(100, custom)).toBe("gold");
    expect(calculateTier(50, custom)).toBe("silver");
    expect(calculateTier(10, custom)).toBe("bronze");
    expect(calculateTier(5, custom)).toBe("none");
  });
});

describe("renderMilesClubBadge", () => {
  it("renders gold badge", () => {
    const html = renderMilesClubBadge("gold");
    expect(html).toContain("Gold Club");
    expect(html).toContain("badge--gold");
  });

  it("returns empty string for none", () => {
    expect(renderMilesClubBadge("none")).toBe("");
  });
});

describe("renderTierProgress", () => {
  it("shows progress toward bronze for new users", () => {
    const html = renderTierProgress(50_000);
    expect(html).toContain("Bronze");
    expect(html).toContain("50,000");
  });

  it("shows max for gold users", () => {
    const html = renderTierProgress(300_000);
    expect(html).toContain("Gold Club");
  });
});
