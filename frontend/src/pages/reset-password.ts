/**
 * Reset password page — set a new password using a reset token.
 */

import { apiFetch } from "../api";

/** Extract query parameters from the current hash URL. */
function getHashParams(): URLSearchParams {
  const hash = window.location.hash.slice(1); // remove '#'
  const queryIndex = hash.indexOf("?");
  if (queryIndex === -1) return new URLSearchParams();
  return new URLSearchParams(hash.slice(queryIndex + 1));
}

export function renderResetPassword(container: HTMLElement): void {
  const params = getHashParams();
  const token = params.get("token") ?? "";

  if (!token) {
    container.innerHTML = `
      <div class="container" style="max-width: 400px; padding-top: var(--space-2xl);">
        <div class="card">
          <h2 class="card-title" style="margin-bottom: var(--space-lg);">Invalid Reset Link</h2>
          <p style="color: var(--color-text-muted);">
            This password reset link is invalid or has expired.
            Please <a href="#/forgot-password">request a new one</a>.
          </p>
        </div>
      </div>
    `;
    return;
  }

  container.innerHTML = `
    <div class="container" style="max-width: 400px; padding-top: var(--space-2xl);">
      <div class="card">
        <h2 class="card-title" style="margin-bottom: var(--space-lg);">Reset Password</h2>
        <form id="reset-form">
          <div style="margin-bottom: var(--space-md);">
            <label for="new-password" style="display: block; margin-bottom: var(--space-xs); font-weight: 500;">New Password</label>
            <input class="input" type="password" id="new-password" required minlength="8" />
            <ul class="password-requirements" style="font-size: 0.75rem; color: var(--color-text-muted); list-style: none; padding: 0; margin: var(--space-xs) 0 0 0;">
              <li data-req="length">✗ 8–128 characters</li>
              <li data-req="uppercase">✗ One uppercase letter</li>
              <li data-req="lowercase">✗ One lowercase letter</li>
              <li data-req="digit">✗ One digit</li>
              <li data-req="special">✗ One special character</li>
            </ul>
          </div>
          <div style="margin-bottom: var(--space-lg);">
            <label for="confirm-password" style="display: block; margin-bottom: var(--space-xs); font-weight: 500;">Confirm Password</label>
            <input class="input" type="password" id="confirm-password" required minlength="8" />
            <p id="match-error" style="color: var(--color-error); font-size: 0.75rem; margin-top: var(--space-xs); display: none;">Passwords do not match</p>
          </div>
          <button type="submit" class="btn btn-primary" style="width: 100%;">Reset Password</button>
          <p id="reset-error" style="color: var(--color-error); margin-top: var(--space-sm); display: none;"></p>
          <p id="reset-success" style="color: var(--color-success); margin-top: var(--space-sm); display: none;"></p>
        </form>
      </div>
    </div>
  `;

  // Live password requirement validation
  const passwordInput = document.getElementById("new-password") as HTMLInputElement;
  const confirmInput = document.getElementById("confirm-password") as HTMLInputElement;
  const matchError = document.getElementById("match-error")!;

  const reqChecks: [string, RegExp | ((v: string) => boolean)][] = [
    ["length", (v: string) => v.length >= 8 && v.length <= 128],
    ["uppercase", /[A-Z]/],
    ["lowercase", /[a-z]/],
    ["digit", /\d/],
    ["special", /[^A-Za-z0-9]/],
  ];

  passwordInput.addEventListener("input", () => {
    const val = passwordInput.value;
    for (const [name, check] of reqChecks) {
      const li = container.querySelector(`[data-req="${name}"]`) as HTMLElement;
      if (!li) continue;
      const passed = typeof check === "function" ? check(val) : check.test(val);
      const label = li.textContent!.slice(2);
      li.textContent = `${passed ? "✓" : "✗"} ${label}`;
      li.style.color = passed ? "var(--color-success, #16a34a)" : "var(--color-text-muted)";
    }
    // Update match indicator if confirm has content
    if (confirmInput.value) {
      matchError.style.display = confirmInput.value !== val ? "block" : "none";
    }
  });

  confirmInput.addEventListener("input", () => {
    matchError.style.display =
      confirmInput.value && confirmInput.value !== passwordInput.value ? "block" : "none";
  });

  const form = document.getElementById("reset-form") as HTMLFormElement;
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const newPassword = passwordInput.value;
    const confirmPassword = confirmInput.value;
    const errorEl = document.getElementById("reset-error")!;
    const successEl = document.getElementById("reset-success")!;
    const submitBtn = form.querySelector("button[type='submit']") as HTMLButtonElement;

    errorEl.style.display = "none";
    successEl.style.display = "none";

    if (newPassword !== confirmPassword) {
      errorEl.textContent = "Passwords do not match";
      errorEl.style.display = "block";
      return;
    }

    submitBtn.disabled = true;
    submitBtn.textContent = "Resetting...";

    try {
      await apiFetch<{ message: string }>("/auth/reset-password", {
        method: "POST",
        body: { token, new_password: newPassword },
      });
      successEl.innerHTML =
        'Password reset successfully! <a href="#/login">Log in</a> with your new password.';
      successEl.style.display = "block";
      form.querySelectorAll("input").forEach((inp) => (inp.disabled = true));
      submitBtn.style.display = "none";
    } catch (err: any) {
      errorEl.textContent = err.message || "Reset failed. The link may have expired.";
      errorEl.style.display = "block";
      submitBtn.disabled = false;
      submitBtn.textContent = "Reset Password";
    }
  });
}
