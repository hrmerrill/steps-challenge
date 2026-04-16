/**
 * User profile page — personal info, all-time stats, and active challenge stats.
 */

import { getCurrentUser, isAuthenticated } from "../auth";
import { navigate } from "../router";
import { apiFetch } from "../api";
import { calculateTier, renderMilesClubBadge } from "../components/miles-club";
import { renderStepChart, DayData } from "../components/step-chart";

interface Challenge {
  id: number;
  name: string;
  description: string | null;
  start_date: string;
  end_date: string;
  is_active: boolean;
  participant_count: number;
}

interface Membership {
  joined: boolean;
  miles_club_tier: string | null;
}

interface UserChallengeStats {
  user_id: number;
  display_name: string;
  challenge_id: number;
  total_steps: number;
  total_miles: number;
  rank: number;
  total_participants: number;
  days_logged: number;
  average_daily: number;
  miles_club_tier: string;
}

interface OverallUserStats {
  user_id: number;
  display_name: string;
  total_steps: number;
  total_miles: number;
  rank: number;
  total_users: number;
  days_logged: number;
  average_daily: number;
}

function formatNumber(n: number): string {
  return n.toLocaleString();
}

export async function renderProfile(container: HTMLElement): Promise<void> {
  if (!isAuthenticated()) {
    navigate("/login");
    return;
  }

  const user = getCurrentUser();

  container.innerHTML = `
    <div class="container" style="max-width: 700px; padding-top: var(--space-xl);">
      <div class="card">
        <h2 class="card-title" style="margin-bottom: var(--space-lg);">Profile</h2>
        <div style="margin-bottom: var(--space-md);">
          <strong>Name:</strong> ${user?.display_name ?? "Unknown"}
        </div>
        <div style="margin-bottom: var(--space-md);">
          <strong>Email:</strong> ${user?.email ?? "Unknown"}
        </div>
        <div style="margin-bottom: var(--space-lg);">
          <strong>Tier:</strong> <span id="profile-tier" style="color: var(--color-text-muted);">—</span>
        </div>
        <div id="profile-stats"></div>
      </div>
      <div id="profile-challenge-stats" style="margin-top: var(--space-lg);"></div>
      <div id="profile-chart" style="margin-top: var(--space-lg);"></div>
    </div>
  `;

  // All-time stats + rank
  try {
    const [summary, overallStats] = await Promise.all([
      apiFetch<{
        total_steps: number;
        total_miles: number;
        days_logged: number;
        average_daily: number;
      }>("/steps/summary"),
      apiFetch<OverallUserStats>("/leaderboard/overall/my-stats"),
    ]);

    const tier = calculateTier(summary.average_daily);
    const tierEl = document.getElementById("profile-tier")!;
    tierEl.innerHTML = `${renderMilesClubBadge(tier)} (${summary.average_daily.toLocaleString()} steps/day)`;

    document.getElementById("profile-stats")!.innerHTML = `
      <h3 style="margin-bottom: var(--space-sm);">Your All-Time Stats</h3>
      <span class="card-subtitle" style="display: block; margin-bottom: var(--space-sm);">Rank ${overallStats.rank} of ${overallStats.total_users}</span>
      <div class="card-grid" style="grid-template-columns: repeat(2, 1fr);">
        <div><strong>${formatNumber(summary.total_steps)}</strong><br/><span style="color: var(--color-text-muted);">Total Steps</span></div>
        <div><strong>${summary.total_miles.toLocaleString()}</strong><br/><span style="color: var(--color-text-muted);">Total Miles</span></div>
        <div><strong>${summary.days_logged}</strong><br/><span style="color: var(--color-text-muted);">Days Logged</span></div>
        <div><strong>${formatNumber(summary.average_daily)}</strong><br/><span style="color: var(--color-text-muted);">Avg Daily Steps</span></div>
      </div>
    `;
  } catch {
    // Profile still renders without stats
  }

  // Active challenge stats
  try {
    const challenges = await apiFetch<Challenge[]>("/challenges/");
    const today = new Date().toISOString().split("T")[0];
    const active = challenges.find(
      (c) => c.start_date <= today && c.end_date >= today,
    );

    if (active) {
      const membership = await apiFetch<Membership>(`/challenges/${active.id}/membership`);
      if (membership.joined) {
        const challengeStats = await apiFetch<UserChallengeStats>(
          `/challenges/${active.id}/my-stats`,
        );

        const tierLabels: Record<string, string> = {
          high: ">10k steps/day",
          mid: "5k\u201310k steps/day",
          low: "0\u20135k steps/day",
          none: "\u2014",
        };
        const tierLabel = tierLabels[challengeStats.miles_club_tier] ?? "\u2014";

        document.getElementById("profile-challenge-stats")!.innerHTML = `
          <div class="card">
            <div class="card-header">
              <h3 class="card-title">Your Stats — ${active.name}</h3>
              <span class="card-subtitle">Rank ${challengeStats.rank} of ${challengeStats.total_participants}</span>
            </div>
            <div class="stats-grid">
              <div class="stat-item">
                <div class="stat-value">${formatNumber(challengeStats.total_steps)}</div>
                <div class="stat-label">Total Steps</div>
              </div>
              <div class="stat-item">
                <div class="stat-value">${challengeStats.total_miles}</div>
                <div class="stat-label">Miles</div>
              </div>
              <div class="stat-item">
                <div class="stat-value">${challengeStats.days_logged}</div>
                <div class="stat-label">Days Logged</div>
              </div>
              <div class="stat-item">
                <div class="stat-value">${formatNumber(challengeStats.average_daily)}</div>
                <div class="stat-label">Avg Daily</div>
              </div>
              <div class="stat-item">
                <div class="stat-value">${tierLabel}</div>
                <div class="stat-label">Miles Club</div>
              </div>
            </div>
          </div>
        `;

        // Personal step chart for the challenge period
        try {
          const steps = await apiFetch<DayData[]>(
            `/steps/?start_date=${active.start_date}&end_date=${active.end_date}`,
          );
          renderStepChart(
            document.getElementById("profile-chart")!,
            steps,
            "Your Steps",
          );
        } catch {
          // Chart is optional
        }
      }
    }
  } catch {
    // Challenge stats are optional
  }
}
