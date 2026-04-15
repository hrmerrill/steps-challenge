/**
 * Tests for trail map component utilities.
 */
import { describe, it, expect } from "vitest";
import {
  interpolatePosition,
  APPALACHIAN_TRAIL_POINTS,
} from "../src/components/trail-map";

describe("interpolatePosition", () => {
  const points: [number, number][] = [
    [0, 0],
    [10, 10],
    [20, 20],
  ];

  it("returns start point at 0%", () => {
    const pos = interpolatePosition(points, 0);
    expect(pos).toEqual([0, 0]);
  });

  it("returns end point at 100%", () => {
    const pos = interpolatePosition(points, 100);
    expect(pos).toEqual([20, 20]);
  });

  it("returns midpoint at 50%", () => {
    const pos = interpolatePosition(points, 50);
    expect(pos[0]).toBe(10);
    expect(pos[1]).toBe(10);
  });

  it("returns 25% position correctly", () => {
    const pos = interpolatePosition(points, 25);
    expect(pos[0]).toBe(5);
    expect(pos[1]).toBe(5);
  });

  it("handles negative progress", () => {
    const pos = interpolatePosition(points, -10);
    expect(pos).toEqual([0, 0]);
  });

  it("handles over 100% progress", () => {
    const pos = interpolatePosition(points, 150);
    expect(pos).toEqual([20, 20]);
  });

  it("works with real trail points", () => {
    const pos = interpolatePosition(APPALACHIAN_TRAIL_POINTS, 50);
    // Should be roughly in the mid-Atlantic region
    expect(pos[0]).toBeGreaterThan(35);
    expect(pos[0]).toBeLessThan(42);
  });
});
