/**
 * Tests for step chart component utilities.
 */
import { describe, it, expect } from "vitest";
import { getMaxSteps, DayData } from "../src/components/step-chart";

describe("getMaxSteps", () => {
  it("returns max from data array", () => {
    const data: DayData[] = [
      { date: "2026-04-15", step_count: 5000 },
      { date: "2026-04-16", step_count: 12000 },
      { date: "2026-04-17", step_count: 8000 },
    ];
    expect(getMaxSteps(data)).toBe(12000);
  });

  it("returns 0 for empty array", () => {
    expect(getMaxSteps([])).toBe(0);
  });

  it("handles single entry", () => {
    const data: DayData[] = [{ date: "2026-04-15", step_count: 10000 }];
    expect(getMaxSteps(data)).toBe(10000);
  });
});
