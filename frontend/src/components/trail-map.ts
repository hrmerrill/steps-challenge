/**
 * Trail map component — Leaflet.js integration for virtual trail progress.
 *
 * Loads the actual Appalachian Trail GeoJSON (sourced from OpenStreetMap) and
 * renders it on an OpenTopoMap with a distance-aware progress marker.
 */

import { apiFetch } from "../api";

export interface TrailProgress {
  total_group_steps: number;
  total_group_miles: number;
  trail_name: string;
  trail_length_miles: number;
  progress_percent: number;
}

/** GeoJSON types used for the trail data. */
interface TrailGeoJSON {
  type: "FeatureCollection";
  features: Array<{
    type: "Feature";
    properties: Record<string, unknown>;
    geometry: { type: "LineString"; coordinates: [number, number][] };
  }>;
}

/**
 * Load the trail GeoJSON and return coordinates as [lat, lng] pairs.
 * GeoJSON stores [lng, lat]; Leaflet expects [lat, lng].
 */
export async function loadTrailCoordinates(): Promise<[number, number][]> {
  const resp = await fetch("/appalachian-trail.geojson");
  if (!resp.ok) throw new Error(`Failed to load trail GeoJSON: ${resp.status}`);
  const geojson: TrailGeoJSON = await resp.json();
  const coords: [number, number][] = [];
  for (const feature of geojson.features) {
    if (feature.geometry.type === "LineString") {
      for (const [lng, lat] of feature.geometry.coordinates) {
        coords.push([lat, lng]);
      }
    }
  }
  return coords;
}

/** Haversine distance between two [lat, lng] points, in miles. */
export function haversineDistance(
  a: [number, number],
  b: [number, number],
): number {
  const R = 3958.8; // Earth radius in miles
  const toRad = Math.PI / 180;
  const dLat = (b[0] - a[0]) * toRad;
  const dLng = (b[1] - a[1]) * toRad;
  const sinLat = Math.sin(dLat / 2);
  const sinLng = Math.sin(dLng / 2);
  const h =
    sinLat * sinLat +
    Math.cos(a[0] * toRad) * Math.cos(b[0] * toRad) * sinLng * sinLng;
  return R * 2 * Math.atan2(Math.sqrt(h), Math.sqrt(1 - h));
}

/** Compute cumulative distances (in miles) along a polyline. */
export function computeCumulativeDistances(
  points: [number, number][],
): number[] {
  const d = [0];
  for (let i = 1; i < points.length; i++) {
    d.push(d[i - 1] + haversineDistance(points[i - 1], points[i]));
  }
  return d;
}

/**
 * Distance-aware interpolation along a polyline.
 *
 * Maps `progressPercent` (0–100) to a [lat, lng] position by computing the
 * proportional distance along the trail rather than the proportional segment
 * index. This ensures the marker moves at a geographically accurate pace.
 *
 * Pass pre-computed `cumulativeDistances` to avoid recalculating each call.
 */
export function interpolatePosition(
  points: [number, number][],
  progressPercent: number,
  cumulativeDistances?: number[],
): [number, number] {
  if (points.length === 0) return [0, 0];
  if (progressPercent <= 0) return points[0];
  if (progressPercent >= 100) return points[points.length - 1];

  const cumDist = cumulativeDistances ?? computeCumulativeDistances(points);
  const totalDist = cumDist[cumDist.length - 1];
  const target = (progressPercent / 100) * totalDist;

  // Binary search for the segment containing the target distance
  let lo = 0;
  let hi = cumDist.length - 1;
  while (lo < hi - 1) {
    const mid = Math.floor((lo + hi) / 2);
    if (cumDist[mid] <= target) lo = mid;
    else hi = mid;
  }

  const segLen = cumDist[hi] - cumDist[lo];
  const t = segLen > 0 ? (target - cumDist[lo]) / segLen : 0;

  return [
    points[lo][0] + (points[hi][0] - points[lo][0]) * t,
    points[lo][1] + (points[hi][1] - points[lo][1]) * t,
  ];
}

/** Render the trail map card. Requires Leaflet loaded globally. */
export async function renderTrailMap(
  container: HTMLElement,
  challengeId: number | "overall",
): Promise<void> {
  try {
    const url =
      challengeId === "overall"
        ? "/leaderboard/overall/trail"
        : `/leaderboard/${challengeId}/trail`;

    // Fetch progress data and trail GeoJSON in parallel
    const [progress, trailCoords] = await Promise.all([
      apiFetch<TrailProgress>(url),
      loadTrailCoordinates(),
    ]);

    container.innerHTML = `
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">${progress.trail_name}</h3>
          <span class="card-subtitle">${progress.total_group_miles.toLocaleString()} mi / ${progress.trail_length_miles.toLocaleString()} mi (${progress.progress_percent}%)</span>
        </div>
        <div id="trail-map" style="height: 400px; border-radius: var(--radius-md);"></div>
      </div>
    `;

    const L = (window as any).L;
    if (!L) {
      container.querySelector("#trail-map")!.innerHTML =
        '<p style="padding: 1rem;">Map requires Leaflet.js</p>';
      return;
    }

    const map = L.map("trail-map").setView([39.0, -77.5], 5);
    L.tileLayer("https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png", {
      attribution:
        '© <a href="https://opentopomap.org">OpenTopoMap</a> · Trail data © <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 17,
    }).addTo(map);

    // Draw the actual trail path
    L.polyline(trailCoords, {
      color: "#4f46e5",
      weight: 3,
      opacity: 0.6,
    }).addTo(map);

    // Start and end markers
    const start = trailCoords[0];
    const end = trailCoords[trailCoords.length - 1];
    L.marker(start).addTo(map).bindPopup("Start: Springer Mountain, GA");
    L.marker(end).addTo(map).bindPopup("End: Mount Katahdin, ME");

    // Progress marker (distance-aware)
    const cumDist = computeCumulativeDistances(trailCoords);
    const pos = interpolatePosition(
      trailCoords,
      progress.progress_percent,
      cumDist,
    );
    L.circleMarker(pos, {
      radius: 10,
      fillColor: "#22c55e",
      color: "#fff",
      weight: 2,
      fillOpacity: 0.9,
    })
      .addTo(map)
      .bindPopup(
        `Group progress: ${progress.total_group_miles.toLocaleString()} miles (${progress.progress_percent}%)`,
      )
      .openPopup();
  } catch {
    container.innerHTML = `<div class="card"><p>Failed to load trail map.</p></div>`;
  }
}
