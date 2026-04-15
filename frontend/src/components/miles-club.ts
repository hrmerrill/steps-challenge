/**
 * Miles club badge/tier display component.
 */

export type MilesClubTier = "gold" | "silver" | "bronze" | "none";

export interface MilesClubThresholds {
  gold: number;
  silver: number;
  bronze: number;
}

/** Default thresholds (match backend config). */
export const DEFAULT_THRESHOLDS: MilesClubThresholds = {
  gold: 300_000,
  silver: 200_000,
  bronze: 100_000,
};

/** Calculate tier from total monthly steps. */
export function calculateTier(
  steps: number,
  thresholds: MilesClubThresholds = DEFAULT_THRESHOLDS,
): MilesClubTier {
  if (steps >= thresholds.gold) return "gold";
  if (steps >= thresholds.silver) return "silver";
  if (steps >= thresholds.bronze) return "bronze";
  return "none";
}

/** Render a miles club badge. */
export function renderMilesClubBadge(tier: MilesClubTier): string {
  const config: Record<MilesClubTier, { emoji: string; label: string; cssClass: string }> = {
    gold: { emoji: "🥇", label: "Gold Club", cssClass: "badge--gold" },
    silver: { emoji: "🥈", label: "Silver Club", cssClass: "badge--silver" },
    bronze: { emoji: "🥉", label: "Bronze Club", cssClass: "badge--bronze" },
    none: { emoji: "", label: "", cssClass: "" },
  };

  const c = config[tier];
  if (!c.label) return "";
  return `<span class="badge ${c.cssClass}">${c.emoji} ${c.label}</span>`;
}

/** Render a progress bar toward the next tier. */
export function renderTierProgress(
  steps: number,
  thresholds: MilesClubThresholds = DEFAULT_THRESHOLDS,
): string {
  const tier = calculateTier(steps, thresholds);
  let nextThreshold: number;
  let nextLabel: string;

  switch (tier) {
    case "none":
      nextThreshold = thresholds.bronze;
      nextLabel = "Bronze";
      break;
    case "bronze":
      nextThreshold = thresholds.silver;
      nextLabel = "Silver";
      break;
    case "silver":
      nextThreshold = thresholds.gold;
      nextLabel = "Gold";
      break;
    case "gold":
      return `<div class="tier-progress">🥇 You've reached Gold Club!</div>`;
  }

  const pct = Math.min((steps / nextThreshold) * 100, 100).toFixed(1);
  return `
    <div class="tier-progress">
      <div>${steps.toLocaleString()} / ${nextThreshold.toLocaleString()} steps to ${nextLabel}</div>
      <div style="background: var(--color-border); border-radius: var(--radius-full); height: 8px; margin-top: 4px;">
        <div style="width: ${pct}%; background: var(--color-primary); border-radius: var(--radius-full); height: 100%;"></div>
      </div>
    </div>
  `;
}
