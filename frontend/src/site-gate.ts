/**
 * Simple site-wide password gate.
 * Blocks all content until the correct shared password is entered.
 * Authenticated state persists in localStorage.
 */

const STORAGE_KEY = "site_authed";
const PASSWORD_HASH =
  "2e2f974bc10e23a1a747f1b0f323b0fcb79e61b3421b903953acc8444bc3592c";

/** Check if user has already passed the gate. */
export function isSiteAuthed(): boolean {
  return localStorage.getItem(STORAGE_KEY) === "1";
}

/** Hash a string with SHA-256 using the Web Crypto API. */
async function sha256(text: string): Promise<string> {
  const data = new TextEncoder().encode(text);
  const buf = await crypto.subtle.digest("SHA-256", data);
  return Array.from(new Uint8Array(buf))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

/** Show the password gate UI. Returns a promise that resolves when auth succeeds. */
export function showGate(root: HTMLElement): Promise<void> {
  return new Promise((resolve) => {
    root.innerHTML = `
      <div style="display:flex;align-items:center;justify-content:center;min-height:100vh;padding:var(--space-lg);">
        <div class="card" style="max-width:380px;width:100%;text-align:center;">
          <h2 class="card-title" style="margin-bottom:var(--space-md);">🥾 Carbon Steps Challenge</h2>
          <p style="color:var(--color-text-muted);margin-bottom:var(--space-lg);font-size:0.875rem;">
            Enter the site password to continue.
          </p>
          <form id="gate-form">
            <input class="input" type="password" id="gate-pw" placeholder="Password" autocomplete="off"
              style="margin-bottom:var(--space-md);" />
            <button type="submit" class="btn btn-primary" style="width:100%;">Enter</button>
            <p id="gate-error" style="color:var(--color-error);margin-top:var(--space-sm);display:none;font-size:0.875rem;"></p>
          </form>
        </div>
      </div>
    `;

    const form = document.getElementById("gate-form") as HTMLFormElement;
    const input = document.getElementById("gate-pw") as HTMLInputElement;
    const error = document.getElementById("gate-error")!;

    input.focus();

    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const hash = await sha256(input.value);
      if (hash === PASSWORD_HASH) {
        localStorage.setItem(STORAGE_KEY, "1");
        resolve();
      } else {
        error.textContent = "Incorrect password";
        error.style.display = "block";
        input.value = "";
        input.focus();
      }
    });
  });
}
