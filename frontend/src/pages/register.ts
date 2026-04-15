/**
 * Register page — create account.
 */

import { register } from "../auth";
import { navigate } from "../router";

export function renderRegister(container: HTMLElement): void {
  container.innerHTML = `
    <div class="container" style="max-width: 480px; padding-top: var(--space-2xl);">
      <div class="card">
        <h2 class="card-title" style="margin-bottom: var(--space-lg);">Create Account</h2>
        <form id="register-form">
          <div style="margin-bottom: var(--space-md);">
            <label for="display-name" style="display: block; margin-bottom: var(--space-xs); font-weight: 500;">Display Name</label>
            <input class="input" type="text" id="display-name" required maxlength="100" />
          </div>
          <div style="margin-bottom: var(--space-md);">
            <label for="email" style="display: block; margin-bottom: var(--space-xs); font-weight: 500;">Email</label>
            <input class="input" type="email" id="email" required />
          </div>
          <div style="margin-bottom: var(--space-lg);">
            <label for="password" style="display: block; margin-bottom: var(--space-xs); font-weight: 500;">Password</label>
            <input class="input" type="password" id="password" required minlength="8" />
            <span style="font-size: 0.75rem; color: var(--color-text-muted);">Minimum 8 characters</span>
          </div>
          <button type="submit" class="btn btn-primary" style="width: 100%;">Create Account</button>
          <p id="register-error" style="color: var(--color-error); margin-top: var(--space-sm); display: none;"></p>
        </form>

        <p style="margin-top: var(--space-lg); text-align: center;">
          Already have an account? <a href="#/login">Login</a>
        </p>
      </div>
    </div>
  `;

  const form = document.getElementById("register-form") as HTMLFormElement;
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const displayName = (document.getElementById("display-name") as HTMLInputElement).value;
    const email = (document.getElementById("email") as HTMLInputElement).value;
    const password = (document.getElementById("password") as HTMLInputElement).value;
    const errorEl = document.getElementById("register-error")!;

    try {
      await register(email, password, displayName);
      navigate("/");
    } catch (err: any) {
      errorEl.textContent = err.message || "Registration failed";
      errorEl.style.display = "block";
    }
  });
}
