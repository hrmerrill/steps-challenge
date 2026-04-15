/**
 * Landing / Dashboard page — leaderboard, trail map, step chart.
 */

import { renderLeaderboard } from "../components/leaderboard";
import { renderTrailMap } from "../components/trail-map";
import { renderStepChart, DayData } from "../components/step-chart";
import { renderMilesClubBadge, calculateTier } from "../components/miles-club";
import { apiFetch } from "../api";
import { isAuthenticated, getCurrentUser } from "../auth";

export async function renderLanding(container: HTMLElement): Promise<void> {
  container.innerHTML = `
    <div class="container" style="padding-top: var(--space-xl);">
      <h1 style="margin-bottom: var(--space-lg);">🚶 Steps Challenge Dashboard</h1>
      <div class="card-grid--wide" style="display: grid; gap: var(--space-lg);">
        <div id="trail-section"></div>
        <div class="card-grid">
          <div id="leaderboard-section"></div>
          <div id="chart-section"></div>
        </div>
      </div>
    </div>
  `;

  // Load active challenge
  try {
    const challenges = await apiFetch<any[]>("/challenges/");
    const active = challenges.find((c) => c.is_active);
    if (!active) {
      document.getElementById("leaderboard-section")!.innerHTML =
        '<div class="card"><p>No active challenge. Create one to get started!</p></div>';
      return;
    }

    // Render components in parallel
    await Promise.all([
      renderLeaderboard(document.getElementById("leaderboard-section")!, active.id),
      renderTrailMap(document.getElementById("trail-section")!, active.id),
    ]);

    // Load user's own step chart if authenticated
    if (isAuthenticated()) {
      const steps = await apiFetch<DayData[]>(
        `/steps/?start_date=${active.start_date}&end_date=${active.end_date}`,
      );
      renderStepChart(document.getElementById("chart-section")!, steps, "Your Steps");
    }
  } catch {
    container.innerHTML += '<div class="card"><p>Failed to load dashboard.</p></div>';
  }
}
