/**
 * User profile page.
 */

import { getCurrentUser, isAuthenticated } from "../auth";
import { navigate } from "../router";
import { apiFetch } from "../api";

export async function renderProfile(container: HTMLElement): Promise<void> {
  if (!isAuthenticated()) {
    navigate("/login");
    return;
  }

  const user = getCurrentUser();

  container.innerHTML = `
    <div class="container" style="max-width: 600px; padding-top: var(--space-xl);">
      <div class="card">
        <h2 class="card-title" style="margin-bottom: var(--space-lg);">Profile</h2>
        <div style="margin-bottom: var(--space-md);">
          <strong>Name:</strong> ${user?.display_name ?? "Unknown"}
        </div>
        <div style="margin-bottom: var(--space-md);">
          <strong>Email:</strong> ${user?.email ?? "Unknown"}
        </div>
        <div style="margin-bottom: var(--space-lg);">
          <strong style="display: block; margin-bottom: var(--space-sm);">Connected Trackers:</strong>
          <div style="margin-bottom: var(--space-md);">
            ${user?.garmin_connected ? "Garmin " : ""}
            ${user?.strava_connected ? "Strava " : ""}
            ${user?.fitbit_connected ? "Fitbit " : ""}
            ${!user?.garmin_connected && !user?.strava_connected && !user?.fitbit_connected ? "<span style='color: var(--color-text-muted)'>None — enter steps manually</span>" : ""}
          </div>
          
          ${(!user?.garmin_connected || !user?.strava_connected || !user?.fitbit_connected) ? `
          <div style="margin-top: var(--space-md); padding-top: var(--space-md); border-top: 1px solid var(--color-border);">
            <p style="font-size: 0.875rem; font-weight: 500; margin-bottom: var(--space-sm);">Connect a Tracker</p>
            <div style="display: flex; gap: var(--space-sm); flex-wrap: wrap;">
              ${!user?.garmin_connected ? `<button class="btn btn-secondary" style="font-size: 0.875rem; padding: 0.25rem 0.5rem;" disabled title="Coming soon">Garmin</button>` : ''}
              ${!user?.strava_connected ? `<button class="btn btn-secondary" style="font-size: 0.875rem; padding: 0.25rem 0.5rem;" disabled title="Coming soon">Strava</button>` : ''}
              ${!user?.fitbit_connected ? `<button class="btn btn-secondary" style="font-size: 0.875rem; padding: 0.25rem 0.5rem;" disabled title="Coming soon">Fitbit</button>` : ''}
            </div>
            <p style="font-size: 0.75rem; color: var(--color-text-muted); margin-top: var(--space-xs);">
              Provider sync coming soon — enter steps manually for now.
            </p>
          </div>
          ` : ''}
        </div>
        <div id="profile-stats"></div>
      </div>
    </div>
  `;

  try {
    const summary = await apiFetch<{
      total_steps: number;
      total_miles: number;
      days_logged: number;
      average_daily: number;
    }>("/steps/summary");

    document.getElementById("profile-stats")!.innerHTML = `
      <h3 style="margin-bottom: var(--space-sm);">All-Time Stats</h3>
      <div class="card-grid" style="grid-template-columns: repeat(2, 1fr);">
        <div><strong>${summary.total_steps.toLocaleString()}</strong><br/><span style="color: var(--color-text-muted);">Total Steps</span></div>
        <div><strong>${summary.total_miles.toLocaleString()}</strong><br/><span style="color: var(--color-text-muted);">Total Miles</span></div>
        <div><strong>${summary.days_logged}</strong><br/><span style="color: var(--color-text-muted);">Days Logged</span></div>
        <div><strong>${summary.average_daily.toLocaleString()}</strong><br/><span style="color: var(--color-text-muted);">Avg Daily Steps</span></div>
      </div>
    `;
  } catch {
    // Ignore — profile still renders without stats
  }
}
