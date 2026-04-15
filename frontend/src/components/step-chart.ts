/**
 * Step chart component — renders daily step bars.
 */

export interface DayData {
  date: string;
  step_count: number;
}

/** Render a simple bar chart of daily steps. */
export function renderStepChart(
  container: HTMLElement,
  data: DayData[],
  title: string = "Daily Steps",
): void {
  if (data.length === 0) {
    container.innerHTML = `
      <div class="card">
        <div class="card-header"><h3 class="card-title">${title}</h3></div>
        <p class="card-subtitle">No step data yet.</p>
      </div>
    `;
    return;
  }

  const maxSteps = Math.max(...data.map((d) => d.step_count));

  const bars = data
    .map((d) => {
      const pct = maxSteps > 0 ? (d.step_count / maxSteps) * 100 : 0;
      const dateLabel = new Date(d.date + "T00:00:00").toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
      });
      return `
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
          <span style="min-width: 60px; font-size: 0.75rem; color: var(--color-text-muted);">${dateLabel}</span>
          <div style="flex: 1; background: var(--color-border); border-radius: var(--radius-sm); height: 20px;">
            <div style="width: ${pct}%; background: var(--color-primary); border-radius: var(--radius-sm); height: 100%; min-width: 2px;"></div>
          </div>
          <span style="min-width: 60px; text-align: right; font-size: 0.75rem; font-variant-numeric: tabular-nums;">${d.step_count.toLocaleString()}</span>
        </div>
      `;
    })
    .join("");

  container.innerHTML = `
    <div class="card">
      <div class="card-header"><h3 class="card-title">📊 ${title}</h3></div>
      ${bars}
    </div>
  `;
}

/** Calculate max steps from data (exported for testing). */
export function getMaxSteps(data: DayData[]): number {
  if (data.length === 0) return 0;
  return Math.max(...data.map((d) => d.step_count));
}
