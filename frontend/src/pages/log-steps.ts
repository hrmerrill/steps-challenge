/**
 * Manual step entry page.
 */

import { apiFetch } from "../api";
import { isAuthenticated } from "../auth";
import { navigate } from "../router";

export function renderLogSteps(container: HTMLElement): void {
  if (!isAuthenticated()) {
    navigate("/login");
    return;
  }

  const today = new Date().toISOString().split("T")[0];

  container.innerHTML = `
    <div class="container" style="max-width: 480px; padding-top: var(--space-xl);">
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
          <button type="submit" class="btn btn-primary" style="width: 100%;">Log Steps</button>
          <p id="log-success" style="color: var(--color-success); margin-top: var(--space-sm); display: none;"></p>
          <p id="log-error" style="color: var(--color-error); margin-top: var(--space-sm); display: none;"></p>
        </form>
      </div>
    </div>
  `;

  const form = document.getElementById("log-form") as HTMLFormElement;
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const date = (document.getElementById("step-date") as HTMLInputElement).value;
    const stepCount = parseInt((document.getElementById("step-count") as HTMLInputElement).value, 10);
    const successEl = document.getElementById("log-success")!;
    const errorEl = document.getElementById("log-error")!;
    successEl.style.display = "none";
    errorEl.style.display = "none";

    try {
      await apiFetch("/steps/", {
        method: "POST",
        body: { date, step_count: stepCount, source: "manual" },
      });
      successEl.textContent = `✅ Logged ${stepCount.toLocaleString()} steps for ${date}`;
      successEl.style.display = "block";
      (document.getElementById("step-count") as HTMLInputElement).value = "";
    } catch (err: any) {
      errorEl.textContent = err.message || "Failed to log steps";
      errorEl.style.display = "block";
    }
  });
}
