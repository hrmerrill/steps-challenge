/**
 * User profile page — personal info, photo upload, step logging,
 * all-time stats, and active challenge stats.
 * Two-column layout: profile info (left) + log steps (right) on desktop;
 * stacked vertically on mobile.
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

interface StepEntry {
  id: number;
  user_id: number;
  date: string;
  step_count: number;
  source: string;
}

function formatNumber(n: number): string {
  return n.toLocaleString();
}

function formatDate(iso: string): string {
  return new Date(iso + "T00:00:00").toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
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

async function loadHistory(historyEl: HTMLElement): Promise<void> {
  try {
    const entries = await apiFetch<StepEntry[]>("/steps/");
    if (entries.length === 0) {
      historyEl.innerHTML = '<p class="card-subtitle">No steps logged yet.</p>';
      return;
    }

    const rows = entries
      .map(
        (e) => `
      <div class="step-history-row" data-id="${e.id}" data-date="${e.date}" data-count="${e.step_count}" data-source="${e.source}">
        <span class="step-history-date">${formatDate(e.date)}</span>
        <span class="step-history-count">${e.step_count.toLocaleString()} steps</span>
        <span class="step-history-source badge ${e.source === "manual" ? "" : "badge--mid"}">${e.source}</span>
        <span class="step-history-actions">
          ${e.source === "manual" ? `<button class="btn btn-secondary btn-sm edit-btn" data-id="${e.id}">Edit</button>` : ""}
          ${e.source === "manual" ? `<button class="btn btn-secondary btn-sm delete-btn" data-id="${e.id}">Delete</button>` : ""}
        </span>
      </div>`,
      )
      .join("");

    historyEl.innerHTML = rows;
  } catch {
    historyEl.innerHTML = '<p style="color: var(--color-error);">Failed to load step history.</p>';
  }
}

export async function renderProfile(container: HTMLElement): Promise<void> {
  if (!isAuthenticated()) {
    navigate("/login");
    return;
  }

  const user = getCurrentUser();
  const today = new Date().toISOString().split("T")[0];

  container.innerHTML = `
    <div class="container" style="padding-top: var(--space-xl);">
      <div class="profile-columns">
        <div class="profile-col-left">
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
            <div id="google-health-section" style="margin-bottom: var(--space-lg); padding: var(--space-md); background: var(--color-surface); border-radius: var(--radius-md); border: 1px solid var(--color-border);">
              <h3 style="margin-bottom: var(--space-sm); font-size: 0.95rem;">Google Health Integration</h3>
              <div id="google-health-controls">Loading…</div>
            </div>
            <div id="profile-stats"></div>
          </div>
          <div id="profile-challenge-stats" style="margin-top: var(--space-lg);"></div>
          <div id="profile-chart" style="margin-top: var(--space-lg);"></div>
        </div>

        <div class="profile-col-right">
          <div class="card">
            <h2 class="card-title" style="margin-bottom: var(--space-lg);">Log Steps</h2>
            <form id="log-form">
              <div style="margin-bottom: var(--space-md);">
                <label for="step-date" style="display: block; margin-bottom: var(--space-xs); font-weight: 500;">Date</label>
                <input class="input" type="date" id="step-date" value="${today}" required />
              </div>
              <div style="margin-bottom: var(--space-lg);">
                <label for="step-count" style="display: block; margin-bottom: var(--space-xs); font-weight: 500;">Steps</label>
                <input class="input" type="number" id="step-count" min="1" max="500000" required placeholder="e.g. 10000" />
              </div>
              <button type="submit" class="btn btn-primary" id="log-submit-btn" style="width: 100%;">Log Steps</button>
              <button type="button" class="btn btn-secondary" id="cancel-edit-btn" style="width: 100%; margin-top: var(--space-xs); display: none;">Cancel Edit</button>
              <p id="log-success" style="color: var(--color-success); margin-top: var(--space-sm); display: none;"></p>
              <p id="log-error" style="color: var(--color-error); margin-top: var(--space-sm); display: none;"></p>
            </form>
          </div>

          <div class="card" style="margin-top: var(--space-lg);">
            <div class="card-header"><h3 class="card-title">Step History</h3></div>
            <div id="step-history">Loading…</div>
          </div>
        </div>
      </div>
    </div>
  `;

  // --- Photo upload handler ---
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
      renderProfile(container);
    } catch (err: any) {
      photoError.textContent = err.message || "Upload failed";
      photoError.style.display = "block";
    }
  });

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

  // --- Google Health integration controls ---
  const googleHealthControls = document.getElementById("google-health-controls")!;

  async function loadGoogleHealthStatus(): Promise<void> {
    try {
      const status = await apiFetch<{
        configured: boolean;
        connected: boolean;
        preferred_step_source: string;
      }>("/google-health/status");

      if (!status.configured) {
        googleHealthControls.innerHTML = '<span style="color: var(--color-text-muted); font-size: 0.85rem;">Google Health integration is not available on this server.</span>';
        return;
      }

      if (status.connected) {
        googleHealthControls.innerHTML = `
          <div style="display: flex; align-items: center; gap: var(--space-sm); flex-wrap: wrap;">
            <span class="badge badge--high">Connected</span>
            <span style="color: var(--color-text-muted); font-size: 0.85rem;">Source: ${status.preferred_step_source}</span>
          </div>
          <div style="display: flex; gap: var(--space-sm); margin-top: var(--space-sm);">
            <button class="btn btn-primary btn-sm" id="google-health-sync-btn">Sync Now</button>
            <button class="btn btn-secondary btn-sm" id="google-health-disconnect-btn">Disconnect</button>
          </div>
          <p id="google-health-message" style="margin-top: var(--space-xs); font-size: 0.85rem; display: none;"></p>
        `;

        document.getElementById("google-health-sync-btn")!.addEventListener("click", async () => {
          const msgEl = document.getElementById("google-health-message")!;
          msgEl.style.display = "none";
          try {
            const result = await apiFetch<{ days_synced: number }>("/google-health/sync", { method: "POST" });
            msgEl.textContent = `Synced ${result.days_synced} days of step data.`;
            msgEl.style.color = "var(--color-success)";
            msgEl.style.display = "block";
            await loadHistory(historyEl);
          } catch (err: any) {
            msgEl.textContent = err.message || "Sync failed";
            msgEl.style.color = "var(--color-error)";
            msgEl.style.display = "block";
          }
        });

        document.getElementById("google-health-disconnect-btn")!.addEventListener("click", async () => {
          if (!confirm("Disconnect Google Health? Your synced step data will be preserved but manual entry will become your primary source.")) return;
          try {
            await apiFetch("/google-health/disconnect", { method: "POST" });
            await fetchMe();
            await loadGoogleHealthStatus();
          } catch (err: any) {
            const msgEl = document.getElementById("google-health-message")!;
            msgEl.textContent = err.message || "Disconnect failed";
            msgEl.style.color = "var(--color-error)";
            msgEl.style.display = "block";
          }
        });
      } else {
        googleHealthControls.innerHTML = `
          <button class="btn btn-primary btn-sm" id="google-health-connect-btn">Connect Google Health</button>
          <p id="google-health-message" style="margin-top: var(--space-xs); font-size: 0.85rem; display: none;"></p>
        `;

        document.getElementById("google-health-connect-btn")!.addEventListener("click", async () => {
          const msgEl = document.getElementById("google-health-message")!;
          try {
            const resp = await apiFetch<{ authorization_url: string }>("/google-health/connect");
            window.location.href = resp.authorization_url;
          } catch (err: any) {
            msgEl.textContent = err.message || "Failed to start Google Health connection";
            msgEl.style.color = "var(--color-error)";
            msgEl.style.display = "block";
          }
        });
      }
    } catch {
      googleHealthControls.innerHTML = '<span style="color: var(--color-text-muted); font-size: 0.85rem;">Could not load Google Health status.</span>';
    }
  }

  loadGoogleHealthStatus();

  // --- Log steps form handler ---
  const form = document.getElementById("log-form") as HTMLFormElement;
  const dateInput = document.getElementById("step-date") as HTMLInputElement;
  const countInput = document.getElementById("step-count") as HTMLInputElement;
  const submitBtn = document.getElementById("log-submit-btn") as HTMLButtonElement;
  const cancelBtn = document.getElementById("cancel-edit-btn") as HTMLButtonElement;
  const successEl = document.getElementById("log-success")!;
  const errorEl = document.getElementById("log-error")!;
  const historyEl = document.getElementById("step-history")!;

  let editingDate: string | null = null;

  function resetForm(): void {
    editingDate = null;
    dateInput.value = today;
    countInput.value = "";
    submitBtn.textContent = "Log Steps";
    cancelBtn.style.display = "none";
    dateInput.readOnly = false;
    successEl.style.display = "none";
    errorEl.style.display = "none";
  }

  cancelBtn.addEventListener("click", resetForm);

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const date = dateInput.value;
    const stepCount = parseInt(countInput.value, 10);
    successEl.style.display = "none";
    errorEl.style.display = "none";

    try {
      await apiFetch("/steps/", {
        method: "POST",
        body: { date, step_count: stepCount, source: "manual" },
      });
      const verb = editingDate ? "Updated" : "Logged";
      successEl.textContent = `${verb} ${stepCount.toLocaleString()} steps for ${formatDate(date)}`;
      successEl.style.display = "block";
      resetForm();
      await loadHistory(historyEl);
    } catch (err: any) {
      errorEl.textContent = err.message || "Failed to log steps";
      errorEl.style.display = "block";
    }
  });

  historyEl.addEventListener("click", async (e) => {
    const target = e.target as HTMLElement;

    if (target.classList.contains("edit-btn")) {
      const row = target.closest(".step-history-row") as HTMLElement;
      editingDate = row.dataset.date!;
      dateInput.value = editingDate;
      countInput.value = row.dataset.count!;
      dateInput.readOnly = true;
      submitBtn.textContent = "Update Steps";
      cancelBtn.style.display = "block";
      successEl.style.display = "none";
      errorEl.style.display = "none";
      countInput.focus();
      return;
    }

    if (target.classList.contains("delete-btn")) {
      const id = target.dataset.id!;
      if (!confirm("Delete this step entry?")) return;
      try {
        await apiFetch(`/steps/${id}`, { method: "DELETE" });
        await loadHistory(historyEl);
      } catch {
        errorEl.textContent = "Failed to delete entry";
        errorEl.style.display = "block";
      }
    }
  });

  // Initial history load
  loadHistory(historyEl);

  // --- All-time stats + rank ---
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

  // --- Active challenge stats ---
  try {
    const challenges = await apiFetch<Challenge[]>("/challenges/");
    const todayStr = new Date().toISOString().split("T")[0];
    const active = challenges.find(
      (c) => c.start_date <= todayStr && c.end_date >= todayStr,
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
