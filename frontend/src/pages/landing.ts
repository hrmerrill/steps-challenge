/**
 * Landing / Dashboard page — join challenge, personal stats, leaderboard, trail map, step chart.
 */

import { renderLeaderboard } from "../components/leaderboard";
import { renderTrailMap } from "../components/trail-map";
import { renderStepChart, DayData } from "../components/step-chart";
import { apiFetch, ApiError } from "../api";
import { isAuthenticated, getCurrentUser } from "../auth";

interface Challenge {
  id: number;
  name: string;
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

function formatNumber(n: number): string {
  return n.toLocaleString();
}

function renderStatsCard(container: HTMLElement, stats: UserChallengeStats): void {
  const tierLabels: Record<string, string> = {
    gold: "🥇 Gold",
    silver: "🥈 Silver",
    bronze: "🥉 Bronze",
    none: "—",
  };
  const tierLabel = tierLabels[stats.miles_club_tier] ?? "—";

  container.innerHTML = `
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">📊 Your Stats</h3>
        <span class="card-subtitle">Rank ${stats.rank} of ${stats.total_participants}</span>
      </div>
      <div class="stats-grid">
        <div class="stat-item">
          <div class="stat-value">${formatNumber(stats.total_steps)}</div>
          <div class="stat-label">Total Steps</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">${stats.total_miles}</div>
          <div class="stat-label">Miles</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">${stats.days_logged}</div>
          <div class="stat-label">Days Logged</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">${formatNumber(stats.average_daily)}</div>
          <div class="stat-label">Avg Daily</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">${tierLabel}</div>
          <div class="stat-label">Miles Club</div>
        </div>
      </div>
    </div>
  `;
}

async function handleJoin(challengeId: number, container: HTMLElement): Promise<void> {
  const btn = container.querySelector<HTMLButtonElement>("#join-btn");
  if (btn) {
    btn.disabled = true;
    btn.textContent = "Joining…";
  }
  try {
    const result = await apiFetch<{ joined: boolean; miles_club_tier: string }>(
      `/challenges/${challengeId}/join`,
      { method: "POST" },
    );
    if (result.joined) {
      // Reload the page to show stats
      window.location.reload();
    }
  } catch (err) {
    const msg = err instanceof ApiError ? err.message : "Failed to join challenge";
    const banner = container.querySelector("#join-section");
    if (banner) {
      banner.innerHTML = `<div class="card"><p style="color: var(--color-error);">${msg}</p></div>`;
    }
  }
}

export async function renderLanding(container: HTMLElement): Promise<void> {
  container.innerHTML = `
    <div class="container" style="padding-top: var(--space-xl);">
      <h1 style="margin-bottom: var(--space-lg);">Steps Challenge Dashboard</h1>
      <div id="join-section"></div>
      <div id="stats-section" style="margin-bottom: var(--space-lg);"></div>
      <div class="card-grid--wide" style="display: grid; gap: var(--space-lg);">
        <div id="trail-section"></div>
        <div class="card-grid">
          <div id="leaderboard-section"></div>
          <div id="chart-section"></div>
        </div>
      </div>
    </div>
  `;

  try {
    const challenges = await apiFetch<Challenge[]>("/challenges/");
    const active = challenges.find((c) => c.is_active);
    if (!active) {
      document.getElementById("leaderboard-section")!.innerHTML =
        '<div class="card"><p>No active challenge. Create one to get started!</p></div>';
      return;
    }

    const user = getCurrentUser();
    let membership: Membership | null = null;
    let userStats: UserChallengeStats | null = null;

    // Check membership and load stats if authenticated
    if (isAuthenticated() && user) {
      try {
        membership = await apiFetch<Membership>(`/challenges/${active.id}/membership`);
      } catch {
        membership = null;
      }

      if (membership?.joined) {
        try {
          userStats = await apiFetch<UserChallengeStats>(`/challenges/${active.id}/my-stats`);
        } catch {
          userStats = null;
        }
      }
    }

    // Show join banner if authenticated but not joined
    const joinSection = document.getElementById("join-section")!;
    if (isAuthenticated() && membership && !membership.joined) {
      joinSection.innerHTML = `
        <div class="join-banner">
          <p>🏃 <strong>${active.name}</strong> is underway! Join the challenge to start tracking your steps.</p>
          <button class="btn btn-primary" id="join-btn">Join Challenge</button>
        </div>
      `;
      const joinBtn = document.getElementById("join-btn")!;
      joinBtn.addEventListener("click", () => handleJoin(active.id, container));
    }

    // Show individual stats if joined
    const statsSection = document.getElementById("stats-section")!;
    if (userStats) {
      renderStatsCard(statsSection, userStats);
    }

    // Render components in parallel
    await Promise.all([
      renderLeaderboard(
        document.getElementById("leaderboard-section")!,
        active.id,
        user?.id,
      ),
      renderTrailMap(document.getElementById("trail-section")!, active.id),
    ]);

    // Load user's own step chart if authenticated and joined
    if (isAuthenticated() && membership?.joined) {
      const steps = await apiFetch<DayData[]>(
        `/steps/?start_date=${active.start_date}&end_date=${active.end_date}`,
      );
      renderStepChart(document.getElementById("chart-section")!, steps, "Your Steps");
    }
  } catch {
    container.innerHTML += '<div class="card"><p>Failed to load dashboard.</p></div>';
  }
}
