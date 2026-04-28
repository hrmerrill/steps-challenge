/**
 * Tests for forgot-password page rendering and form submission.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

vi.mock("../src/api", () => ({
  apiFetch: vi.fn(),
}));

vi.mock("../src/router", () => ({
  navigate: vi.fn(),
}));

import { renderForgotPassword } from "../src/pages/forgot-password";
import { apiFetch } from "../src/api";

describe("Forgot password page", () => {
  let container: HTMLElement;

  beforeEach(() => {
    container = document.createElement("div");
    document.body.appendChild(container);
    renderForgotPassword(container);
  });

  afterEach(() => {
    container.remove();
    vi.restoreAllMocks();
  });

  it("renders email input and submit button", () => {
    expect(container.querySelector("#email")).toBeTruthy();
    expect(container.querySelector("button[type='submit']")).toBeTruthy();
    expect(container.querySelector("button[type='submit']")!.textContent).toBe("Send Reset Link");
  });

  it("renders a link back to login", () => {
    const link = container.querySelector('a[href="#/login"]');
    expect(link).toBeTruthy();
    expect(link!.textContent).toBe("Back to login");
  });

  it("shows success message after submission", async () => {
    vi.mocked(apiFetch).mockResolvedValue({
      message: "If an account exists with that email, you will receive a password reset link.",
    });

    const emailInput = container.querySelector("#email") as HTMLInputElement;
    emailInput.value = "test@example.com";

    const form = container.querySelector("#forgot-form") as HTMLFormElement;
    form.dispatchEvent(new Event("submit", { cancelable: true }));

    // Wait for async handler
    await vi.waitFor(() => {
      const successEl = container.querySelector("#forgot-success") as HTMLElement;
      expect(successEl.style.display).toBe("block");
    });
  });

  it("shows error message on API failure", async () => {
    vi.mocked(apiFetch).mockRejectedValue(new Error("Network error"));

    const emailInput = container.querySelector("#email") as HTMLInputElement;
    emailInput.value = "test@example.com";

    const form = container.querySelector("#forgot-form") as HTMLFormElement;
    form.dispatchEvent(new Event("submit", { cancelable: true }));

    await vi.waitFor(() => {
      const errorEl = container.querySelector("#forgot-error") as HTMLElement;
      expect(errorEl.style.display).toBe("block");
      expect(errorEl.textContent).toBe("Network error");
    });
  });
});
