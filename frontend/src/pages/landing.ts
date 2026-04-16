/**
 * Landing / Dashboard page — challenge selector, status banner, join, team stats,
 * leaderboard, trail map. Supports per-challenge and overall views.
 */

import { renderLeaderboard } from "../components/leaderboard";
import { renderTrailMap } from "../components/trail-map";
import { apiFetch, ApiError } from "../api";
import { isAuthenticated, getCurrentUser } from "../auth";

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

interface TeamChallengeStats {
  challenge_id: number;
  total_steps: number;
  total_miles: number;
  total_participants: number;
  total_days_logged: number;
  average_daily_per_participant: number;
}

interface OverallTeamStats {
  total_steps: number;
  total_miles: number;
  total_users: number;
  total_days_logged: number;
  average_daily_per_user: number;
}

type ChallengeStatus = "upcoming" | "active" | "ended";

function formatNumber(n: number): string {
  return n.toLocaleString();
}

function getChallengeStatus(challenge: Challenge): ChallengeStatus {
  const today = new Date().toISOString().split("T")[0];
  if (challenge.start_date > today) return "upcoming";
  if (challenge.end_date < today) return "ended";
  return "active";
}

function daysUntil(dateStr: string): number {
  const target = new Date(dateStr + "T00:00:00");
  const now = new Date();
  now.setHours(0, 0, 0, 0);
  return Math.ceil((target.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
}

function renderStatusBanner(challenge: Challenge): string {
  const status = getChallengeStatus(challenge);
  const infoBtn = `<button class="how-it-works-toggle" id="how-it-works-btn" title="How It Works">How It Works</button>`;
  if (status === "upcoming") {
    const days = daysUntil(challenge.start_date);
    return `<div class="challenge-status challenge-status--upcoming">
      <span><strong>${challenge.name}</strong> starts in ${days} day${days === 1 ? "" : "s"} (${challenge.start_date})</span>
      ${infoBtn}
    </div>`;
  }
  if (status === "active") {
    const daysLeft = daysUntil(challenge.end_date);
    return `<div class="challenge-status challenge-status--active">
      <span><strong>${challenge.name}</strong> is underway — ${daysLeft} day${daysLeft === 1 ? "" : "s"} remaining</span>
      ${infoBtn}
    </div>`;
  }
  return `<div class="challenge-status challenge-status--ended">
    <span><strong>${challenge.name}</strong> has ended (${challenge.start_date} – ${challenge.end_date})</span>
    ${infoBtn}
  </div>`;
}

function formatDate(dateStr: string): string {
  const d = new Date(dateStr + "T00:00:00");
  return d.toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" });
}

function renderHowItWorks(challenge: Challenge): string {
  const start = formatDate(challenge.start_date);
  const end = formatDate(challenge.end_date);
  const descriptionHtml = challenge.description
    ? `<p style="margin-bottom: var(--space-md);">${challenge.description}</p>`
    : "";

  return `
    <div class="how-it-works-card" id="how-it-works-card" style="display: none;">
      <div class="card">
        <div class="card-header" style="display: flex; align-items: center; justify-content: space-between;">
          <h3 class="card-title">How It Works</h3>
          <button class="how-it-works-close" id="how-it-works-close" title="Close">&times;</button>
        </div>
        <div style="padding: 0 var(--space-lg) var(--space-lg);">
          ${descriptionHtml}
          <div class="how-it-works-section">
            <h4>Challenge Period</h4>
            <p>This challenge runs from <strong>${start}</strong> to <strong>${end}</strong>. Only steps logged during this window count toward the leaderboard and trail progress.</p>
          </div>
          <div class="how-it-works-section">
            <h4>Miles Clubs</h4>
            <p>When you join, you're placed into a tier based on your <strong>average daily steps from the previous month</strong>:</p>
            <ul class="how-it-works-tiers">
              <li><span class="badge badge--high">&gt;10k steps/day</span> averaged 10,000+ steps/day</li>
              <li><span class="badge badge--mid">5k\u201310k steps/day</span> averaged 5,000\u201310,000 steps/day</li>
              <li><span class="badge badge--low">0\u20135k steps/day</span> averaged under 5,000 steps/day</li>
            </ul>
            <p>Tiers create fair competition groups so everyone can compete with peers at a similar activity level.</p>
          </div>
          <div class="how-it-works-section">
            <h4>Virtual Trail Map</h4>
            <p>The group's collective steps are converted to miles (<strong>2,000 steps = 1 mile</strong>) and plotted on the <strong>Appalachian Trail</strong> (2,190 miles). Watch the group advance together!</p>
          </div>
          <div class="how-it-works-section">
            <h4>Leaderboard</h4>
            <p>Individual participants are ranked by total steps. Your personal miles and daily averages are tracked so you can see your progress over time.</p>
          </div>
          <div class="how-it-works-section">
            <h4>Logging Steps</h4>
            <p>Log your steps manually each day. You can edit or delete entries anytime from the Log Steps page.</p>
          </div>
        </div>
      </div>
    </div>
  `;
}

function renderTeamStatsCard(container: HTMLElement, stats: TeamChallengeStats): void {
  container.innerHTML = `
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">Team Stats</h3>
        <span class="card-subtitle">${stats.total_participants} participant${stats.total_participants === 1 ? "" : "s"}</span>
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
          <div class="stat-value">${stats.total_days_logged}</div>
          <div class="stat-label">Days Logged</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">${formatNumber(stats.average_daily_per_participant)}</div>
          <div class="stat-label">Avg Daily</div>
        </div>
      </div>
    </div>
  `;
}

function renderOverallTeamStatsCard(container: HTMLElement, stats: OverallTeamStats): void {
  container.innerHTML = `
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">Team Stats</h3>
        <span class="card-subtitle">${stats.total_users} user${stats.total_users === 1 ? "" : "s"} all-time</span>
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
          <div class="stat-value">${stats.total_days_logged}</div>
          <div class="stat-label">Days Logged</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">${formatNumber(stats.average_daily_per_user)}</div>
          <div class="stat-label">Avg Daily</div>
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

async function renderChallengeView(
  container: HTMLElement,
  challenge: Challenge,
  challenges: Challenge[],
): Promise<void> {
  const user = getCurrentUser();
  const status = getChallengeStatus(challenge);

  // Challenge selector
  const options = challenges
    .map((c) => {
      const selected = c.id === challenge.id ? "selected" : "";
      const tag = getChallengeStatus(c) === "active" ? " (Active)" : getChallengeStatus(c) === "upcoming" ? " (Upcoming)" : "";
      return `<option value="${c.id}" ${selected}>${c.name}${tag}</option>`;
    })
    .join("");

  container.innerHTML = `
    <div class="container" style="padding-top: var(--space-xl);">
      <h1 style="margin-bottom: var(--space-md);">Steps Challenge Dashboard</h1>
      <div class="challenge-selector">
        <label for="challenge-select">View:</label>
        <select id="challenge-select">
          ${options}
          <option value="overall">Overall Progress</option>
        </select>
      </div>
      <div id="status-section"></div>
      <div id="info-section"></div>
      <div id="join-section"></div>
      <div id="stats-section" style="margin-bottom: var(--space-lg);"></div>
      <div class="card-grid--wide" style="display: grid; gap: var(--space-lg);">
        <div id="trail-section"></div>
        <div id="leaderboard-section"></div>
      </div>
    </div>
  `;

  // Wire up selector
  document.getElementById("challenge-select")!.addEventListener("change", (e) => {
    const val = (e.target as HTMLSelectElement).value;
    if (val === "overall") {
      renderOverallView(container, challenges);
    } else {
      const selected = challenges.find((c) => c.id === parseInt(val, 10));
      if (selected) renderChallengeView(container, selected, challenges);
    }
  });

  // Status banner
  document.getElementById("status-section")!.innerHTML = renderStatusBanner(challenge);

  // How It Works section
  document.getElementById("info-section")!.innerHTML = renderHowItWorks(challenge);
  const infoCard = document.getElementById("how-it-works-card")!;
  document.getElementById("how-it-works-btn")!.addEventListener("click", () => {
    infoCard.style.display = infoCard.style.display === "none" ? "block" : "none";
  });
  document.getElementById("how-it-works-close")!.addEventListener("click", () => {
    infoCard.style.display = "none";
  });

  let membership: Membership | null = null;

  if (isAuthenticated() && user) {
    try {
      membership = await apiFetch<Membership>(`/challenges/${challenge.id}/membership`);
    } catch {
      membership = null;
    }
  }

  // Join banner (only for active or upcoming challenges)
  const joinSection = document.getElementById("join-section")!;
  if (isAuthenticated() && membership && !membership.joined && status !== "ended") {
    const actionText = status === "upcoming"
      ? `<strong>${challenge.name}</strong> hasn't started yet — join now so you're ready!`
      : `<strong>${challenge.name}</strong> is underway! Join the challenge to start tracking your steps.`;
    joinSection.innerHTML = `
      <div class="join-banner">
        <p>${actionText}</p>
        <button class="btn btn-primary" id="join-btn">Join Challenge</button>
      </div>
    `;
    document.getElementById("join-btn")!.addEventListener("click", () =>
      handleJoin(challenge.id, container),
    );
  }

  // Team stats (visible to everyone, no auth required)
  const statsSection = document.getElementById("stats-section")!;
  try {
    const teamStats = await apiFetch<TeamChallengeStats>(`/challenges/${challenge.id}/team-stats`);
    renderTeamStatsCard(statsSection, teamStats);
  } catch {
    statsSection.innerHTML = '<div class="card"><p>Failed to load team stats.</p></div>';
  }

  // Leaderboard + trail in parallel
  await Promise.all([
    renderLeaderboard(
      document.getElementById("leaderboard-section")!,
      challenge.id,
      user?.id,
    ),
    renderTrailMap(document.getElementById("trail-section")!, challenge.id),
  ]);
}

async function renderOverallView(
  container: HTMLElement,
  challenges: Challenge[],
): Promise<void> {
  const user = getCurrentUser();

  const options = challenges
    .map((c) => {
      const tag = getChallengeStatus(c) === "active" ? " (Active)" : getChallengeStatus(c) === "upcoming" ? " (Upcoming)" : "";
      return `<option value="${c.id}">${c.name}${tag}</option>`;
    })
    .join("");

  container.innerHTML = `
    <div class="container" style="padding-top: var(--space-xl);">
      <h1 style="margin-bottom: var(--space-md);">Steps Challenge Dashboard</h1>
      <div class="challenge-selector">
        <label for="challenge-select">View:</label>
        <select id="challenge-select">
          ${options}
          <option value="overall" selected>Overall Progress</option>
        </select>
      </div>
      <div id="stats-section" style="margin-bottom: var(--space-lg);"></div>
      <div class="card-grid--wide" style="display: grid; gap: var(--space-lg);">
        <div id="trail-section"></div>
        <div id="leaderboard-section"></div>
      </div>
    </div>
  `;

  // Wire up selector
  document.getElementById("challenge-select")!.addEventListener("change", (e) => {
    const val = (e.target as HTMLSelectElement).value;
    if (val === "overall") {
      renderOverallView(container, challenges);
    } else {
      const selected = challenges.find((c) => c.id === parseInt(val, 10));
      if (selected) renderChallengeView(container, selected, challenges);
    }
  });

  // Leaderboard + trail + team stats in parallel (always shown, no auth needed)
  const teamStatsPromise = apiFetch<OverallTeamStats>("/leaderboard/overall/team-stats")
    .then((stats) => renderOverallTeamStatsCard(document.getElementById("stats-section")!, stats))
    .catch(() => {
      document.getElementById("stats-section")!.innerHTML =
        '<div class="card"><p>Failed to load team stats.</p></div>';
    });

  await Promise.all([
    renderLeaderboard(
      document.getElementById("leaderboard-section")!,
      "overall",
      user?.id,
    ),
    renderTrailMap(document.getElementById("trail-section")!, "overall"),
    teamStatsPromise,
  ]);
}

export async function renderLanding(container: HTMLElement): Promise<void> {
  container.innerHTML = `
    <div class="container" style="padding-top: var(--space-xl);">
      <h1 style="margin-bottom: var(--space-lg);">Steps Challenge Dashboard</h1>
      <p>Loading…</p>
    </div>
  `;

  try {
    const challenges = await apiFetch<Challenge[]>("/challenges/");
    if (challenges.length === 0) {
      container.innerHTML = `
        <div class="container" style="padding-top: var(--space-xl);">
          <h1 style="margin-bottom: var(--space-lg);">Steps Challenge Dashboard</h1>
          <div class="card"><p>No challenges yet. Create one to get started!</p></div>
        </div>
      `;
      return;
    }

    // Pick the best default: active challenge, then upcoming, then most recent
    const active = challenges.find((c) => getChallengeStatus(c) === "active");
    const upcoming = challenges.find((c) => getChallengeStatus(c) === "upcoming");
    const defaultChallenge = active ?? upcoming ?? challenges[0];

    await renderChallengeView(container, defaultChallenge, challenges);
  } catch {
    container.innerHTML += '<div class="card"><p>Failed to load dashboard.</p></div>';
  }
}

// Exported for testing
export { getChallengeStatus, daysUntil };
