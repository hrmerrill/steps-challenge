/**
 * Tests for register page password requirements display and live validation.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

vi.mock("../src/auth", () => ({
  register: vi.fn(),
  isAuthenticated: vi.fn(() => false),
}));

vi.mock("../src/api", () => ({
  apiUpload: vi.fn(),
  apiFetch: vi.fn(),
}));

vi.mock("../src/router", () => ({
  navigate: vi.fn(),
}));

import { renderRegister } from "../src/pages/register";

describe("Register page password requirements", () => {
  let container: HTMLElement;

  beforeEach(() => {
    container = document.createElement("div");
    document.body.appendChild(container);
    renderRegister(container);
  });

  afterEach(() => {
    container.remove();
  });

  it("shows all five password requirement items", () => {
    const items = container.querySelectorAll("[data-req]");
    expect(items.length).toBe(5);

    const reqs = Array.from(items).map((el) => el.getAttribute("data-req"));
    expect(reqs).toContain("length");
    expect(reqs).toContain("uppercase");
    expect(reqs).toContain("lowercase");
    expect(reqs).toContain("digit");
    expect(reqs).toContain("special");
  });

  it("initially shows all requirements as unmet", () => {
    const items = container.querySelectorAll("[data-req]");
    for (const item of items) {
      expect(item.textContent).toMatch(/^✗/);
    }
  });

  it("updates requirement indicators on password input", () => {
    const passwordInput = container.querySelector("#password") as HTMLInputElement;

    // Type a password that meets all requirements
    passwordInput.value = "StrongP@ss1";
    passwordInput.dispatchEvent(new Event("input"));

    const items = container.querySelectorAll("[data-req]");
    for (const item of items) {
      expect(item.textContent).toMatch(/^✓/);
    }
  });

  it("shows partial completion correctly", () => {
    const passwordInput = container.querySelector("#password") as HTMLInputElement;

    // Only lowercase, no uppercase/digit/special, too short
    passwordInput.value = "abc";
    passwordInput.dispatchEvent(new Event("input"));

    expect(container.querySelector("[data-req='length']")!.textContent).toMatch(/^✗/);
    expect(container.querySelector("[data-req='uppercase']")!.textContent).toMatch(/^✗/);
    expect(container.querySelector("[data-req='lowercase']")!.textContent).toMatch(/^✓/);
    expect(container.querySelector("[data-req='digit']")!.textContent).toMatch(/^✗/);
    expect(container.querySelector("[data-req='special']")!.textContent).toMatch(/^✗/);
  });

  it("updates when requirements become unmet again", () => {
    const passwordInput = container.querySelector("#password") as HTMLInputElement;

    // Meet all requirements
    passwordInput.value = "StrongP@ss1";
    passwordInput.dispatchEvent(new Event("input"));
    expect(container.querySelector("[data-req='uppercase']")!.textContent).toMatch(/^✓/);

    // Remove uppercase
    passwordInput.value = "strongp@ss1";
    passwordInput.dispatchEvent(new Event("input"));
    expect(container.querySelector("[data-req='uppercase']")!.textContent).toMatch(/^✗/);
    expect(container.querySelector("[data-req='lowercase']")!.textContent).toMatch(/^✓/);
  });
});
