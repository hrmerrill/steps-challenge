/**
 * User profile page — personal info, photo upload, all-time stats, and active challenge stats.
 */

import { getCurrentUser, isAuthenticated, fetchMe } from "../auth";
import { navigate } from "../router";
import { apiFetch, apiUpload } from "../api";
import { renderMilesClubBadge, MilesClubTier } from "../components/miles-club";
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
  miles_club_tier: string;
  miles_club_average_daily: number;
}

function formatNumber(n: number): string {
  return n.toLocaleString();
}

function getInitials(name: string): string {
  return name
    .split(/\s+/)
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase() ?? "")
    .join("");
}

function renderAvatarHtml(photoUrl: string | null | undefined, displayName: string): string {
  if (photoUrl) {
    return `<img src="${photoUrl}" alt="${displayName}" class="avatar-img" />`;
  }
  return `<span class="avatar-initials">${getInitials(displayName)}</span>`;
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
        <div style="display: flex; align-items: center; gap: var(--space-lg); margin-bottom: var(--space-lg); flex-wrap: wrap;">
          <div style="display: flex; flex-direction: column; align-items: center; gap: var(--space-sm);">
            <div id="profile-avatar" class="avatar avatar--xl">
              ${renderAvatarHtml(user?.profile_photo_url, user?.display_name ?? "?")}
            </div>
            <div style="display: flex; gap: var(--space-xs);">
              <label class="btn btn-secondary btn-sm" style="cursor: pointer;">
                ${user?.profile_photo_url ? "Change" : "Upload"} Photo
                <input type="file" id="photo-input" accept="image/jpeg,image/png,image/webp,image/gif" style="display: none;" />
              </label>
              ${user?.profile_photo_url ? '<button id="remove-photo-btn" class="btn btn-secondary btn-sm">Remove</button>' : ""}
            </div>
            <p id="photo-error" style="color: var(--color-error); font-size: 0.75rem; display: none;"></p>
          </div>
          <div style="flex: 1;">
            <div style="margin-bottom: var(--space-sm);">
              <strong>Name:</strong> ${user?.display_name ?? "Unknown"}
            </div>
            <div style="margin-bottom: var(--space-sm);">
              <strong>Email:</strong> ${user?.email ?? "Unknown"}
            </div>
            <div>
              <strong>Tier:</strong> <span id="profile-tier" style="color: var(--color-text-muted);">—</span>
            </div>
          </div>
        </div>
        <div id="profile-stats"></div>
      </div>
      <div id="profile-challenge-stats" style="margin-top: var(--space-lg);"></div>
      <div id="profile-chart" style="margin-top: var(--space-lg);"></div>
    </div>
  `;

  // Photo upload handler
  const photoInput = document.getElementById("photo-input") as HTMLInputElement;
  const photoError = document.getElementById("photo-error")!;
  const avatarEl = document.getElementById("profile-avatar")!;

  photoInput.addEventListener("change", async () => {
    const file = photoInput.files?.[0];
    if (!file) return;
    photoError.style.display = "none";

    try {
      const resp = await apiUpload<{ profile_photo_url: string }>("/auth/profile-photo", file);
      avatarEl.innerHTML = `<img src="${resp.profile_photo_url}" alt="Profile" class="avatar-img" />`;
      await fetchMe();
      // Re-render to update buttons
      renderProfile(container);
    } catch (err: any) {
      photoError.textContent = err.message || "Upload failed";
      photoError.style.display = "block";
    }
  });

  // Remove photo handler
  const removeBtn = document.getElementById("remove-photo-btn");
  if (removeBtn) {
    removeBtn.addEventListener("click", async () => {
      photoError.style.display = "none";
      try {
        await apiFetch("/auth/profile-photo", { method: "DELETE" });
        await fetchMe();
        renderProfile(container);
      } catch (err: any) {
        photoError.textContent = err.message || "Remove failed";
        photoError.style.display = "block";
      }
    });
  }

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

    const tier = overallStats.miles_club_tier as MilesClubTier;
    const tierAvg = overallStats.miles_club_average_daily;
    const tierEl = document.getElementById("profile-tier")!;
    tierEl.innerHTML = `${renderMilesClubBadge(tier)} (${tierAvg.toLocaleString()} steps/day avg last month)`;

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
