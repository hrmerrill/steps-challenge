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
          <strong>Step Entry:</strong> <span style="color: var(--color-text-muted);">Manual</span>
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
