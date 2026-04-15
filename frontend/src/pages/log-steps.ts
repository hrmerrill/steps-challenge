/**
 * Manual step entry page — log new steps + view/edit/delete history.
 */

import { apiFetch } from "../api";
import { isAuthenticated } from "../auth";
import { navigate } from "../router";

interface StepEntry {
  id: number;
  user_id: number;
  date: string;
  step_count: number;
  source: string;
}

function formatDate(iso: string): string {
  return new Date(iso + "T00:00:00").toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
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
        <span class="step-history-source badge ${e.source === "manual" ? "" : "badge--bronze"}">${e.source}</span>
        <span class="step-history-actions">
          ${e.source === "manual" ? `<button class="btn btn-secondary btn-sm edit-btn" data-id="${e.id}">Edit</button>` : ""}
          <button class="btn btn-secondary btn-sm delete-btn" data-id="${e.id}">Delete</button>
        </span>
      </div>`,
      )
      .join("");

    historyEl.innerHTML = rows;
  } catch {
    historyEl.innerHTML = '<p style="color: var(--color-error);">Failed to load step history.</p>';
  }
}

export function renderLogSteps(container: HTMLElement): void {
  if (!isAuthenticated()) {
    navigate("/login");
    return;
  }

  const today = new Date().toISOString().split("T")[0];

  container.innerHTML = `
    <div class="container" style="max-width: 560px; padding-top: var(--space-xl);">
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
  `;

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

  // Delegate edit/delete clicks on history rows
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

  // Initial load
  loadHistory(historyEl);
}
