/**
 * Leaderboard card component with profile photo thumbnails.
 */

import { apiFetch } from "../api";

export interface LeaderboardEntry {
  rank: number;
  user_id: number;
  display_name: string;
  profile_photo_url: string | null;
  total_steps: number;
  miles_club_tier: string;
  total_miles: number;
}

const TIER_BADGE: Record<string, { label: string; class: string }> = {
  high: { label: ">10k steps/day", class: "badge--high" },
  mid: { label: "5k\u201310k steps/day", class: "badge--mid" },
  low: { label: "0\u20135k steps/day", class: "badge--low" },
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

/** Get initials for avatar fallback. */
function getInitials(name: string): string {
  return name
    .split(/\s+/)
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase() ?? "")
    .join("");
}

/** Render a small avatar (thumbnail or initials). Clickable when photo exists. */
export function avatarHtml(photoUrl: string | null | undefined, displayName: string): string {
  if (photoUrl) {
    return `<button class="avatar avatar--sm avatar--clickable" type="button" data-photo-url="${photoUrl}" data-display-name="${displayName}" aria-label="View ${displayName}'s photo"><img src="${photoUrl}" alt="${displayName}" class="avatar-img" /></button>`;
  }
  return `<span class="avatar avatar--sm"><span class="avatar-initials">${getInitials(displayName)}</span></span>`;
}

/** Create and show a modal with the full-size profile photo. */
export function openPhotoModal(photoUrl: string, displayName: string): HTMLElement {
  closePhotoModal();

  const overlay = document.createElement("div");
  overlay.className = "photo-modal-overlay";
  overlay.setAttribute("role", "dialog");
  overlay.setAttribute("aria-label", `${displayName}'s profile photo`);
  overlay.innerHTML = `
    <div class="photo-modal">
      <button class="photo-modal-close" type="button" aria-label="Close">&times;</button>
      <img src="${photoUrl}" alt="${displayName}" class="photo-modal-img" />
      <p class="photo-modal-name">${displayName}</p>
    </div>
  `;

  overlay.addEventListener("click", (e) => {
    if (e.target === overlay) closePhotoModal();
  });
  overlay.querySelector(".photo-modal-close")!.addEventListener("click", () => closePhotoModal());

  const keyHandler = (e: KeyboardEvent) => {
    if (e.key === "Escape") {
      closePhotoModal();
      document.removeEventListener("keydown", keyHandler);
    }
  };
  document.addEventListener("keydown", keyHandler);

  document.body.appendChild(overlay);
  return overlay;
}

/** Remove photo modal from the DOM. */
export function closePhotoModal(): void {
  document.querySelector(".photo-modal-overlay")?.remove();
}

/** Render the leaderboard card into a container. Highlights currentUserId if provided. */
export async function renderLeaderboard(
  container: HTMLElement,
  challengeId: number | "overall",
  currentUserId?: number,
): Promise<void> {
  try {
    const url = challengeId === "overall"
      ? "/leaderboard/overall"
      : `/leaderboard/${challengeId}`;
    const entries = await apiFetch<LeaderboardEntry[]>(url);

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
      .map((e) => {
        const isCurrentUser = currentUserId != null && e.user_id === currentUserId;
        const rowClass = isCurrentUser
          ? "leaderboard-row leaderboard-row--current"
          : "leaderboard-row";
        const youTag = isCurrentUser ? ' <span class="leaderboard-you">You</span>' : "";
        return `
        <div class="${rowClass}">
          <span class="leaderboard-rank">${e.rank}</span>
          ${avatarHtml(e.profile_photo_url, e.display_name)}
          <span class="leaderboard-name">${e.display_name}${youTag} ${tierBadgeHtml(e.miles_club_tier)}</span>
          <span class="leaderboard-steps">${formatSteps(e.total_steps)} steps</span>
        </div>
      `;
      })
      .join("");

    container.innerHTML = `
      <div class="card">
        <div class="card-header"><h3 class="card-title">Leaderboard</h3></div>
        ${rows}
      </div>
    `;

    container.querySelectorAll<HTMLElement>(".avatar--clickable").forEach((el) => {
      el.addEventListener("click", () => {
        const url = el.dataset.photoUrl;
        const name = el.dataset.displayName;
        if (url && name) openPhotoModal(url, name);
      });
    });
  } catch {
    container.innerHTML = `<div class="card"><p>Failed to load leaderboard.</p></div>`;
  }
}
