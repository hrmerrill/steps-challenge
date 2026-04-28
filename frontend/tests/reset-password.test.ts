/**
 * Tests for reset-password page rendering, token extraction, and form validation.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

vi.mock("../src/api", () => ({
  apiFetch: vi.fn(),
}));

vi.mock("../src/router", () => ({
  navigate: vi.fn(),
}));

import { renderResetPassword } from "../src/pages/reset-password";
import { apiFetch } from "../src/api";

describe("Reset password page", () => {
  let container: HTMLElement;

  afterEach(() => {
    container?.remove();
    vi.restoreAllMocks();
    window.location.hash = "";
  });

  function setup(hash = "#/reset-password?token=test-token-123") {
    window.location.hash = hash;
    container = document.createElement("div");
    document.body.appendChild(container);
    renderResetPassword(container);
  }

  it("shows invalid link message when no token is provided", () => {
    setup("#/reset-password");
    expect(container.textContent).toContain("Invalid Reset Link");
    expect(container.querySelector("#reset-form")).toBeFalsy();
  });

  it("renders password form when token is present", () => {
    setup();
    expect(container.querySelector("#new-password")).toBeTruthy();
    expect(container.querySelector("#confirm-password")).toBeTruthy();
    expect(container.querySelector("button[type='submit']")!.textContent).toBe("Reset Password");
  });

  it("shows all five password requirement items", () => {
    setup();
    const items = container.querySelectorAll("[data-req]");
    expect(items.length).toBe(5);
  });

  it("updates password requirement indicators on input", () => {
    setup();
    const passwordInput = container.querySelector("#new-password") as HTMLInputElement;

    passwordInput.value = "StrongP@ss1";
    passwordInput.dispatchEvent(new Event("input"));

    const items = container.querySelectorAll("[data-req]");
    for (const item of items) {
      expect(item.textContent).toMatch(/^✓/);
    }
  });

  it("shows mismatch error when passwords differ", () => {
    setup();
    const passwordInput = container.querySelector("#new-password") as HTMLInputElement;
    const confirmInput = container.querySelector("#confirm-password") as HTMLInputElement;

    passwordInput.value = "StrongP@ss1";
    passwordInput.dispatchEvent(new Event("input"));
    confirmInput.value = "Different@pass2";
    confirmInput.dispatchEvent(new Event("input"));

    const matchError = container.querySelector("#match-error") as HTMLElement;
    expect(matchError.style.display).toBe("block");
  });

  it("hides mismatch error when passwords match", () => {
    setup();
    const passwordInput = container.querySelector("#new-password") as HTMLInputElement;
    const confirmInput = container.querySelector("#confirm-password") as HTMLInputElement;

    passwordInput.value = "StrongP@ss1";
    passwordInput.dispatchEvent(new Event("input"));
    confirmInput.value = "StrongP@ss1";
    confirmInput.dispatchEvent(new Event("input"));

    const matchError = container.querySelector("#match-error") as HTMLElement;
    expect(matchError.style.display).toBe("none");
  });

  it("prevents submission when passwords do not match", async () => {
    setup();
    const passwordInput = container.querySelector("#new-password") as HTMLInputElement;
    const confirmInput = container.querySelector("#confirm-password") as HTMLInputElement;

    passwordInput.value = "StrongP@ss1";
    confirmInput.value = "Different@pass2";

    const form = container.querySelector("#reset-form") as HTMLFormElement;
    form.dispatchEvent(new Event("submit", { cancelable: true }));

    // apiFetch should not have been called
    expect(apiFetch).not.toHaveBeenCalled();

    const errorEl = container.querySelector("#reset-error") as HTMLElement;
    expect(errorEl.style.display).toBe("block");
    expect(errorEl.textContent).toBe("Passwords do not match");
  });

  it("shows success message on successful reset", async () => {
    setup();
    vi.mocked(apiFetch).mockResolvedValue({ message: "Password reset successfully" });

    const passwordInput = container.querySelector("#new-password") as HTMLInputElement;
    const confirmInput = container.querySelector("#confirm-password") as HTMLInputElement;

    passwordInput.value = "NewSecure@pass1";
    confirmInput.value = "NewSecure@pass1";

    const form = container.querySelector("#reset-form") as HTMLFormElement;
    form.dispatchEvent(new Event("submit", { cancelable: true }));

    await vi.waitFor(() => {
      const successEl = container.querySelector("#reset-success") as HTMLElement;
      expect(successEl.style.display).toBe("block");
      expect(successEl.textContent).toContain("successfully");
    });
  });

  it("shows error message on failed reset", async () => {
    setup();
    vi.mocked(apiFetch).mockRejectedValue(new Error("Reset token is invalid or has expired"));

    const passwordInput = container.querySelector("#new-password") as HTMLInputElement;
    const confirmInput = container.querySelector("#confirm-password") as HTMLInputElement;

    passwordInput.value = "NewSecure@pass1";
    confirmInput.value = "NewSecure@pass1";

    const form = container.querySelector("#reset-form") as HTMLFormElement;
    form.dispatchEvent(new Event("submit", { cancelable: true }));

    await vi.waitFor(() => {
      const errorEl = container.querySelector("#reset-error") as HTMLElement;
      expect(errorEl.style.display).toBe("block");
      expect(errorEl.textContent).toContain("invalid");
    });
  });
});
