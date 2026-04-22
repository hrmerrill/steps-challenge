#!/usr/bin/env python3
"""
Fetch the Appalachian Trail from OpenStreetMap (Overpass API) and save as
simplified GeoJSON for the Steps Challenge trail map.

The AT is OSM relation 156553. This script:
  1. Fetches the relation with full geometry via Overpass API
  2. Assembles member ways into an ordered coordinate list
  3. Filters to main route only (skips alternate/approach roles)
  4. Simplifies with iterative Ramer-Douglas-Peucker
  5. Outputs a GeoJSON FeatureCollection with a single LineString
"""

import json
import math
import os
import sys
import urllib.request

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
AT_RELATION_ID = 156553
RDP_TOLERANCE = 0.002  # ~150-200m — good detail for zoom 6-10
OUTPUT_PATH = os.path.join(
    os.path.dirname(__file__), "..", "frontend", "public", "appalachian-trail.geojson"
)


def fetch_at_data() -> dict:
    """Fetch AT relation with full recursion and geometry from Overpass API.

    The AT is a super-relation containing sub-relations (one per state/section),
    which in turn contain the actual ways. We use `>>` to recursively resolve
    all sub-relations down to their ways, then fetch geometry for the ways.
    """
    query = f"""
    [out:json][timeout:300];
    relation({AT_RELATION_ID});
    relation(r);
    way(r);
    out geom;
    """
    req = urllib.request.Request(
        OVERPASS_URL,
        data=f"data={query}".encode(),
        headers={"User-Agent": "StepsChallenge/1.0 (trail-data-fetch)"},
        method="POST",
    )
    print("  Sending Overpass query (may take 1-3 minutes)...")
    with urllib.request.urlopen(req, timeout=360) as resp:
        return json.loads(resp.read())


SPRINGER_MTN = (34.6267, -84.1938)  # Southern terminus


def assemble_ways(elements: list[dict]) -> list[tuple[float, float]]:
    """Assemble way elements into a single ordered coordinate list (lat, lon).

    `elements` is the flat list of way elements returned by the recursive
    Overpass query (not nested inside a relation). We start from the way
    closest to Springer Mountain (southern terminus) and greedily extend
    northward so the resulting line runs south → north.
    """
    ways: list[list[tuple[float, float]]] = []
    for el in elements:
        if el.get("type") != "way":
            continue
        if "geometry" not in el:
            continue
        coords = [(pt["lat"], pt["lon"]) for pt in el["geometry"]]
        if len(coords) >= 2:
            ways.append(coords)

    if not ways:
        raise ValueError("No ways with geometry found in Overpass response")

    # Find the way whose endpoint is closest to Springer Mountain
    best_idx = 0
    best_dist = float("inf")
    best_reverse = False
    for i, way in enumerate(ways):
        d_start = _sq_dist(SPRINGER_MTN, way[0])
        d_end = _sq_dist(SPRINGER_MTN, way[-1])
        if d_start < best_dist:
            best_dist = d_start
            best_idx = i
            best_reverse = False
        if d_end < best_dist:
            best_dist = d_end
            best_idx = i
            best_reverse = True

    first_way = ways[best_idx]
    if best_reverse:
        first_way = list(reversed(first_way))
    assembled = list(first_way)
    used = {best_idx}

    for _ in range(len(ways) - 1):
        end = assembled[-1]
        best_idx = None
        best_reverse = False
        best_dist = float("inf")

        for i, way in enumerate(ways):
            if i in used:
                continue
            d_start = _sq_dist(end, way[0])
            d_end = _sq_dist(end, way[-1])
            if d_start < best_dist:
                best_dist = d_start
                best_idx = i
                best_reverse = False
            if d_end < best_dist:
                best_dist = d_end
                best_idx = i
                best_reverse = True

        if best_idx is None:
            break
        # Stop if nearest way is too far (gap → avoids cross-map jumps)
        if best_dist > 0.01:
            break
        used.add(best_idx)
        way = ways[best_idx]
        if best_reverse:
            way = list(reversed(way))
        # Skip first point if it matches current end (avoid duplicates)
        start = 1 if _sq_dist(assembled[-1], way[0]) < 1e-10 else 0
        assembled.extend(way[start:])

    return assembled


def _sq_dist(a: tuple[float, float], b: tuple[float, float]) -> float:
    """Squared Euclidean distance in degree-space (for matching only)."""
    return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2


def rdp_simplify(
    points: list[tuple[float, float]], epsilon: float
) -> list[tuple[float, float]]:
    """Iterative Ramer-Douglas-Peucker line simplification."""
    n = len(points)
    if n <= 2:
        return list(points)

    keep = [False] * n
    keep[0] = True
    keep[-1] = True
    stack = [(0, n - 1)]

    while stack:
        start, end = stack.pop()
        dmax = 0.0
        index = start
        for i in range(start + 1, end):
            d = _perp_distance(points[i], points[start], points[end])
            if d > dmax:
                dmax = d
                index = i
        if dmax > epsilon:
            keep[index] = True
            if index - start > 1:
                stack.append((start, index))
            if end - index > 1:
                stack.append((index, end))

    return [p for p, k in zip(points, keep) if k]


def _perp_distance(
    point: tuple[float, float],
    line_start: tuple[float, float],
    line_end: tuple[float, float],
) -> float:
    """Perpendicular distance from point to line segment (in degree-space)."""
    dx = line_end[0] - line_start[0]
    dy = line_end[1] - line_start[1]
    mag_sq = dx * dx + dy * dy
    if mag_sq == 0:
        return math.sqrt(
            (point[0] - line_start[0]) ** 2 + (point[1] - line_start[1]) ** 2
        )
    t = max(
        0,
        min(
            1,
            ((point[0] - line_start[0]) * dx + (point[1] - line_start[1]) * dy)
            / mag_sq,
        ),
    )
    cx = line_start[0] + t * dx
    cy = line_start[1] + t * dy
    return math.sqrt((point[0] - cx) ** 2 + (point[1] - cy) ** 2)


def remove_start_loop(
    coords: list[tuple[float, float]], tolerance: float = 0.0005
) -> list[tuple[float, float]]:
    """Remove out-and-back approach trail at the start.

    If the starting coordinate appears again later in the list (within
    *tolerance* degrees), everything before that second occurrence is an
    approach trail loop and gets trimmed.
    """
    start = coords[0]
    for i in range(1, min(len(coords), 200)):
        if abs(coords[i][0] - start[0]) < tolerance and abs(coords[i][1] - start[1]) < tolerance:
            return coords[i:]
    return coords


def to_geojson(coords: list[tuple[float, float]]) -> dict:
    """Convert (lat, lon) coordinate list to a GeoJSON FeatureCollection."""
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "name": "Appalachian Trail",
                    "source": "OpenStreetMap (relation 156553)",
                    "license": "ODbL",
                },
                "geometry": {
                    "type": "LineString",
                    # GeoJSON coordinate order is [longitude, latitude]
                    "coordinates": [
                        [round(lon, 5), round(lat, 5)] for lat, lon in coords
                    ],
                },
            }
        ],
    }


def main() -> None:
    print("Fetching AT data from Overpass API (this may take 1-3 minutes)...")
    data = fetch_at_data()

    elements = data.get("elements", [])
    if not elements:
        print("ERROR: No data returned from Overpass API", file=sys.stderr)
        sys.exit(1)

    way_count = sum(1 for e in elements if e.get("type") == "way")
    print(f"Got {len(elements)} elements ({way_count} ways)")

    print("Assembling ways...")
    coords = assemble_ways(elements)
    print(f"Assembled {len(coords):,} points")

    print("Removing approach-trail loops...")
    coords = remove_start_loop(coords)
    print(f"  {len(coords):,} points after loop removal")

    print(f"Simplifying (RDP tolerance={RDP_TOLERANCE})...")
    simplified = rdp_simplify(coords, RDP_TOLERANCE)
    print(f"Simplified to {len(simplified):,} points")

    geojson = to_geojson(simplified)
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(geojson, f)

    size = os.path.getsize(OUTPUT_PATH)
    print(f"Saved to {OUTPUT_PATH} ({size:,} bytes / {size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
