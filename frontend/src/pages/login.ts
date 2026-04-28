/**
 * Login page.
 */

import { login } from "../auth";
import { navigate } from "../router";

export function renderLogin(container: HTMLElement): void {
  container.innerHTML = `
    <div class="container" style="max-width: 400px; padding-top: var(--space-2xl);">
      <div class="card">
        <h2 class="card-title" style="margin-bottom: var(--space-lg);">Login</h2>
        <form id="login-form">
          <div style="margin-bottom: var(--space-md);">
            <label for="email" style="display: block; margin-bottom: var(--space-xs); font-weight: 500;">Email</label>
            <input class="input" type="email" id="email" required />
          </div>
          <div style="margin-bottom: var(--space-lg);">
            <label for="password" style="display: block; margin-bottom: var(--space-xs); font-weight: 500;">Password</label>
            <input class="input" type="password" id="password" required minlength="8" />
          </div>
          <button type="submit" class="btn btn-primary" style="width: 100%;">Login</button>
          <p id="login-error" style="color: var(--color-error); margin-top: var(--space-sm); display: none;"></p>
        </form>
        <p style="margin-top: var(--space-md); text-align: center;">
          <a href="#/forgot-password">Forgot your password?</a>
        </p>
        <p style="margin-top: var(--space-sm); text-align: center;">
          Don't have an account? <a href="#/register">Sign up</a>
        </p>
      </div>
    </div>
  `;

  const form = document.getElementById("login-form") as HTMLFormElement;
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = (document.getElementById("email") as HTMLInputElement).value;
    const password = (document.getElementById("password") as HTMLInputElement).value;
    const errorEl = document.getElementById("login-error")!;

    try {
      await login(email, password);
      navigate("/");
    } catch (err: any) {
      errorEl.textContent = err.message || "Login failed";
      errorEl.style.display = "block";
    }
  });
}
