/**
 * Tests for trail map component utilities.
 */
import { describe, it, expect } from "vitest";
import {
  interpolatePosition,
  haversineDistance,
  computeCumulativeDistances,
} from "../src/components/trail-map";

describe("haversineDistance", () => {
  it("returns 0 for identical points", () => {
    expect(haversineDistance([40, -74], [40, -74])).toBe(0);
  });

  it("computes a known distance (NYC to DC ≈ 204 mi)", () => {
    const d = haversineDistance([40.7128, -74.006], [38.9072, -77.0369]);
    expect(d).toBeGreaterThan(190);
    expect(d).toBeLessThan(220);
  });

  it("is symmetric", () => {
    const a: [number, number] = [34.63, -84.19];
    const b: [number, number] = [45.90, -68.92];
    expect(haversineDistance(a, b)).toBeCloseTo(haversineDistance(b, a), 10);
  });
});

describe("computeCumulativeDistances", () => {
  it("returns [0] for a single point", () => {
    expect(computeCumulativeDistances([[0, 0]])).toEqual([0]);
  });

  it("returns monotonically increasing values", () => {
    const points: [number, number][] = [
      [34.63, -84.19],
      [36.63, -81.52],
      [39.33, -77.74],
      [45.90, -68.92],
    ];
    const d = computeCumulativeDistances(points);
    expect(d).toHaveLength(4);
    expect(d[0]).toBe(0);
    for (let i = 1; i < d.length; i++) {
      expect(d[i]).toBeGreaterThan(d[i - 1]);
    }
  });
});

describe("interpolatePosition", () => {
  // Use points with known haversine relationships
  const points: [number, number][] = [
    [0, 0],
    [10, 0],
    [20, 0],
  ];

  it("returns start point at 0%", () => {
    const pos = interpolatePosition(points, 0);
    expect(pos).toEqual([0, 0]);
  });

  it("returns end point at 100%", () => {
    const pos = interpolatePosition(points, 100);
    expect(pos).toEqual([20, 0]);
  });

  it("returns midpoint at 50% for equidistant segments", () => {
    // Points along the same meridian have roughly equal-length segments,
    // so 50% by distance ≈ the middle point
    const pos = interpolatePosition(points, 50);
    expect(pos[0]).toBeCloseTo(10, 0);
    expect(pos[1]).toBeCloseTo(0, 5);
  });

  it("handles negative progress", () => {
    const pos = interpolatePosition(points, -10);
    expect(pos).toEqual([0, 0]);
  });

  it("handles over 100% progress", () => {
    const pos = interpolatePosition(points, 150);
    expect(pos).toEqual([20, 0]);
  });

  it("handles empty points array", () => {
    const pos = interpolatePosition([], 50);
    expect(pos).toEqual([0, 0]);
  });

  it("accepts pre-computed cumulative distances", () => {
    const cumDist = computeCumulativeDistances(points);
    const pos = interpolatePosition(points, 50, cumDist);
    expect(pos[0]).toBeCloseTo(10, 0);
  });

  it("places 25% roughly at quarter distance", () => {
    const pos = interpolatePosition(points, 25);
    // Should be around lat 5 (quarter of the way from 0 to 20)
    expect(pos[0]).toBeCloseTo(5, 0);
  });

  it("works with real AT-scale coordinates", () => {
    const atSample: [number, number][] = [
      [34.63, -84.19], // Springer Mtn
      [39.33, -77.74], // Harpers Ferry
      [45.90, -68.92], // Katahdin
    ];
    const pos = interpolatePosition(atSample, 50);
    // 50% by distance should be roughly mid-trail
    expect(pos[0]).toBeGreaterThan(35);
    expect(pos[0]).toBeLessThan(43);
  });
});
