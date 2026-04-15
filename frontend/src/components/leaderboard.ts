/**
 * Leaderboard card component.
 */

import { apiFetch } from "../api";

export interface LeaderboardEntry {
  rank: number;
  user_id: number;
  display_name: string;
  total_steps: number;
  miles_club_tier: string;
  total_miles: number;
}

const TIER_BADGE: Record<string, { label: string; class: string }> = {
  gold: { label: "🥇 Gold", class: "badge--gold" },
  silver: { label: "🥈 Silver", class: "badge--silver" },
  bronze: { label: "🥉 Bronze", class: "badge--bronze" },
  none: { label: "", class: "" },
};

/** Format a step count with thousands separators. */
export function formatSteps(steps: number): string {
  return steps.toLocaleString();
}

/** Get badge HTML for a miles club tier. */
export function tierBadgeHtml(tier: string): string {
  const badge = TIER_BADGE[tier] ?? TIER_BADGE["none"];
  if (!badge.label) return "";
  return `<span class="badge ${badge.class}">${badge.label}</span>`;
}

/** Render the leaderboard card into a container. */
export async function renderLeaderboard(
  container: HTMLElement,
  challengeId: number,
): Promise<void> {
  try {
    const entries = await apiFetch<LeaderboardEntry[]>(
      `/leaderboard/${challengeId}`,
    );

    if (entries.length === 0) {
      container.innerHTML = `
        <div class="card">
          <div class="card-header"><h3 class="card-title">Leaderboard</h3></div>
          <p class="card-subtitle">No participants yet. Join the challenge!</p>
        </div>
      `;
      return;
    }

    const rows = entries
      .map(
        (e) => `
        <div class="leaderboard-row">
          <span class="leaderboard-rank">${e.rank}</span>
          <span class="leaderboard-name">${e.display_name} ${tierBadgeHtml(e.miles_club_tier)}</span>
          <span class="leaderboard-steps">${formatSteps(e.total_steps)} steps</span>
        </div>
      `,
      )
      .join("");

    container.innerHTML = `
      <div class="card">
        <div class="card-header"><h3 class="card-title">🏆 Leaderboard</h3></div>
        ${rows}
      </div>
    `;
  } catch {
    container.innerHTML = `<div class="card"><p>Failed to load leaderboard.</p></div>`;
  }
}
