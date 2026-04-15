/**
 * Trail map component — Leaflet.js integration for virtual trail progress.
 *
 * Renders an OpenStreetMap with the trail route and a progress marker.
 */

import { apiFetch } from "../api";

export interface TrailProgress {
  total_group_steps: number;
  total_group_miles: number;
  trail_name: string;
  trail_length_miles: number;
  progress_percent: number;
}

// Simplified Appalachian Trail waypoints (start → end)
// Springer Mountain, GA to Mount Katahdin, ME
export const APPALACHIAN_TRAIL_POINTS: [number, number][] = [
  [34.6267, -84.1938], // Springer Mountain, GA
  [35.2117, -83.5417], // Fontana Dam, NC
  [35.7117, -83.5133], // Clingmans Dome, TN/NC
  [36.6333, -81.5167], // Damascus, VA
  [37.7833, -79.4500], // Rockfish Gap, VA
  [39.3283, -77.7417], // Harpers Ferry, WV
  [40.9667, -75.1167], // Delaware Water Gap, PA
  [41.5275, -74.0361], // Bear Mountain, NY
  [42.6833, -73.1667], // Bennington, VT
  [44.2706, -71.3033], // White Mountains, NH
  [45.9044, -68.9214], // Mount Katahdin, ME
];

/** Interpolate position along the trail based on progress percentage. */
export function interpolatePosition(
  points: [number, number][],
  progressPercent: number,
): [number, number] {
  if (progressPercent <= 0) return points[0];
  if (progressPercent >= 100) return points[points.length - 1];

  const totalSegments = points.length - 1;
  const position = (progressPercent / 100) * totalSegments;
  const segmentIndex = Math.floor(position);
  const segmentProgress = position - segmentIndex;

  const start = points[segmentIndex];
  const end = points[Math.min(segmentIndex + 1, points.length - 1)];

  return [
    start[0] + (end[0] - start[0]) * segmentProgress,
    start[1] + (end[1] - start[1]) * segmentProgress,
  ];
}

/** Render the trail map card. Requires Leaflet loaded globally. */
export async function renderTrailMap(
  container: HTMLElement,
  challengeId: number | "overall",
): Promise<void> {
  try {
    const url = challengeId === "overall"
      ? "/leaderboard/overall/trail"
      : `/leaderboard/${challengeId}/trail`;
    const progress = await apiFetch<TrailProgress>(url);

    container.innerHTML = `
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">🗺️ ${progress.trail_name}</h3>
          <span class="card-subtitle">${progress.total_group_miles.toLocaleString()} mi / ${progress.trail_length_miles.toLocaleString()} mi (${progress.progress_percent}%)</span>
        </div>
        <div id="trail-map" style="height: 400px; border-radius: var(--radius-md);"></div>
      </div>
    `;

    // Initialize Leaflet map if available
    const L = (window as any).L;
    if (!L) {
      container.querySelector("#trail-map")!.innerHTML =
        '<p style="padding: 1rem;">Map requires Leaflet.js</p>';
      return;
    }

    const map = L.map("trail-map").setView([39.0, -77.5], 5);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "© OpenStreetMap contributors",
      maxZoom: 18,
    }).addTo(map);

    // Draw trail polyline
    L.polyline(APPALACHIAN_TRAIL_POINTS, {
      color: "#4f46e5",
      weight: 3,
      opacity: 0.6,
    }).addTo(map);

    // Add start and end markers
    L.marker(APPALACHIAN_TRAIL_POINTS[0]).addTo(map).bindPopup("Start: Springer Mountain, GA");
    L.marker(APPALACHIAN_TRAIL_POINTS[APPALACHIAN_TRAIL_POINTS.length - 1])
      .addTo(map)
      .bindPopup("End: Mount Katahdin, ME");

    // Progress marker
    const pos = interpolatePosition(
      APPALACHIAN_TRAIL_POINTS,
      progress.progress_percent,
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
