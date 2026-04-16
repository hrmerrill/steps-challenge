/**
 * Register page — create account with optional profile photo.
 */

import { register } from "../auth";
import { apiUpload } from "../api";
import { navigate } from "../router";

/** Generate initials from display name for the default avatar. */
function getInitials(name: string): string {
  return name
    .split(/\s+/)
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase() ?? "")
    .join("");
}

export function renderRegister(container: HTMLElement): void {
  container.innerHTML = `
    <div class="container" style="max-width: 480px; padding-top: var(--space-2xl);">
      <div class="card">
        <h2 class="card-title" style="margin-bottom: var(--space-lg);">Create Account</h2>
        <form id="register-form">
          <div style="display: flex; flex-direction: column; align-items: center; margin-bottom: var(--space-lg);">
            <div id="photo-preview" class="avatar avatar--xl" style="margin-bottom: var(--space-sm);">
              <span class="avatar-initials">?</span>
            </div>
            <label class="btn btn-secondary btn-sm" style="cursor: pointer;">
              Add Photo (optional)
              <input type="file" id="photo-input" accept="image/jpeg,image/png,image/webp,image/gif" style="display: none;" />
            </label>
          </div>
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

  let selectedFile: File | null = null;

  const photoInput = document.getElementById("photo-input") as HTMLInputElement;
  const previewEl = document.getElementById("photo-preview")!;
  const displayNameInput = document.getElementById("display-name") as HTMLInputElement;

  // Update initials preview when display name changes
  displayNameInput.addEventListener("input", () => {
    if (!selectedFile) {
      const initials = getInitials(displayNameInput.value) || "?";
      previewEl.innerHTML = `<span class="avatar-initials">${initials}</span>`;
    }
  });

  photoInput.addEventListener("change", () => {
    const file = photoInput.files?.[0];
    if (file) {
      selectedFile = file;
      const url = URL.createObjectURL(file);
      previewEl.innerHTML = `<img src="${url}" alt="Preview" class="avatar-img" />`;
    }
  });

  const form = document.getElementById("register-form") as HTMLFormElement;
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const displayName = displayNameInput.value;
    const email = (document.getElementById("email") as HTMLInputElement).value;
    const password = (document.getElementById("password") as HTMLInputElement).value;
    const errorEl = document.getElementById("register-error")!;

    try {
      await register(email, password, displayName);

      // Upload photo after account creation (non-blocking on failure)
      if (selectedFile) {
        try {
          await apiUpload("/auth/profile-photo", selectedFile);
        } catch {
          // Photo upload failure shouldn't block registration
        }
      }

      navigate("/");
    } catch (err: any) {
      errorEl.textContent = err.message || "Registration failed";
      errorEl.style.display = "block";
    }
  });
}
