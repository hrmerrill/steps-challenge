/**
 * Miles club badge/tier display component.
 */

export type MilesClubTier = "high" | "mid" | "low" | "none";

export interface MilesClubThresholds {
  high: number;
  mid: number;
}

/** Default thresholds in average daily steps (match backend config). */
export const DEFAULT_THRESHOLDS: MilesClubThresholds = {
  high: 10_000,
  mid: 5_000,
};

/** Calculate tier from average daily steps. */
export function calculateTier(
  averageDailySteps: number,
  thresholds: MilesClubThresholds = DEFAULT_THRESHOLDS,
): MilesClubTier {
  if (averageDailySteps >= thresholds.high) return "high";
  if (averageDailySteps >= thresholds.mid) return "mid";
  return "low";
}

/** Render a miles club badge. */
export function renderMilesClubBadge(tier: MilesClubTier): string {
  const config: Record<MilesClubTier, { label: string; cssClass: string }> = {
    high: { label: ">10k steps/day", cssClass: "badge--high" },
    mid: { label: "5k\u201310k steps/day", cssClass: "badge--mid" },
    low: { label: "0\u20135k steps/day", cssClass: "badge--low" },
    none: { label: "", cssClass: "" },
  };

  const c = config[tier];
  if (!c.label) return "";
  return `<span class="badge ${c.cssClass}">${c.label}</span>`;
}

/** Render a progress bar toward the next tier. */
export function renderTierProgress(
  averageDailySteps: number,
  thresholds: MilesClubThresholds = DEFAULT_THRESHOLDS,
): string {
  const tier = calculateTier(averageDailySteps, thresholds);

  if (tier === "high") {
    return `<div class="tier-progress">You've reached the highest tier!</div>`;
  }

  const nextThreshold = tier === "low" ? thresholds.mid : thresholds.high;
  const nextLabel = tier === "low" ? "5k\u201310k steps/day" : ">10k steps/day";

  const pct = Math.min((averageDailySteps / nextThreshold) * 100, 100).toFixed(1);
  return `
    <div class="tier-progress">
      <div>${averageDailySteps.toLocaleString()} / ${nextThreshold.toLocaleString()} avg steps/day to ${nextLabel}</div>
      <div style="background: var(--color-border); border-radius: var(--radius-full); height: 8px; margin-top: 4px;">
        <div style="width: ${pct}%; background: var(--color-primary); border-radius: var(--radius-full); height: 100%;"></div>
      </div>
    </div>
  `;
}
