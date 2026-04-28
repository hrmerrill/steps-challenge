/**
 * Forgot password page — request a password reset email.
 */

import { apiFetch } from "../api";

export function renderForgotPassword(container: HTMLElement): void {
  container.innerHTML = `
    <div class="container" style="max-width: 400px; padding-top: var(--space-2xl);">
      <div class="card">
        <h2 class="card-title" style="margin-bottom: var(--space-lg);">Forgot Password</h2>
        <p style="color: var(--color-text-muted); margin-bottom: var(--space-lg);">
          Enter your email address and we'll send you a link to reset your password.
        </p>
        <form id="forgot-form">
          <div style="margin-bottom: var(--space-lg);">
            <label for="email" style="display: block; margin-bottom: var(--space-xs); font-weight: 500;">Email</label>
            <input class="input" type="email" id="email" required />
          </div>
          <button type="submit" class="btn btn-primary" style="width: 100%;">Send Reset Link</button>
          <p id="forgot-error" style="color: var(--color-error); margin-top: var(--space-sm); display: none;"></p>
          <p id="forgot-success" style="color: var(--color-success); margin-top: var(--space-sm); display: none;"></p>
        </form>
        <p style="margin-top: var(--space-md); text-align: center;">
          <a href="#/login">Back to login</a>
        </p>
      </div>
    </div>
  `;

  const form = document.getElementById("forgot-form") as HTMLFormElement;
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = (document.getElementById("email") as HTMLInputElement).value;
    const errorEl = document.getElementById("forgot-error")!;
    const successEl = document.getElementById("forgot-success")!;
    const submitBtn = form.querySelector("button[type='submit']") as HTMLButtonElement;

    errorEl.style.display = "none";
    successEl.style.display = "none";
    submitBtn.disabled = true;
    submitBtn.textContent = "Sending...";

    try {
      await apiFetch<{ message: string }>("/auth/forgot-password", {
        method: "POST",
        body: { email },
      });
      successEl.textContent =
        "If an account exists with that email, you will receive a password reset link.";
      successEl.style.display = "block";
      form.querySelector("fieldset, button[type='submit']");
      submitBtn.textContent = "Email Sent";
    } catch (err: any) {
      errorEl.textContent = err.message || "Something went wrong. Please try again.";
      errorEl.style.display = "block";
      submitBtn.disabled = false;
      submitBtn.textContent = "Send Reset Link";
    }
  });
}
