/**
 * Tests for the site-wide password gate.
 */

import { describe, it, expect, beforeEach, vi } from "vitest";

// Mock Web Crypto API (not available in jsdom)
const mockDigest = vi.fn();
Object.defineProperty(globalThis, "crypto", {
  value: {
    subtle: { digest: mockDigest },
  },
  writable: true,
});

// SHA-256 of "CarbonSteps2026!"
const CORRECT_HASH = "2e2f974bc10e23a1a747f1b0f323b0fcb79e61b3421b903953acc8444bc3592c";

function hexToBytes(hex: string): Uint8Array {
  const bytes = new Uint8Array(hex.length / 2);
  for (let i = 0; i < hex.length; i += 2) {
    bytes[i / 2] = parseInt(hex.substring(i, i + 2), 16);
  }
  return bytes;
}

describe("site-gate", () => {
  beforeEach(() => {
    localStorage.clear();
    document.body.innerHTML = '<div id="app"></div>';
    mockDigest.mockReset();
  });

  it("isSiteAuthed returns false when not authed", async () => {
    const { isSiteAuthed } = await import("../src/site-gate");
    expect(isSiteAuthed()).toBe(false);
  });

  it("isSiteAuthed returns true when localStorage flag set", async () => {
    localStorage.setItem("site_authed", "1");
    const { isSiteAuthed } = await import("../src/site-gate");
    expect(isSiteAuthed()).toBe(true);
  });

  it("showGate renders password form", async () => {
    const { showGate } = await import("../src/site-gate");
    const root = document.getElementById("app")!;
    // Don't await — just trigger render
    showGate(root);
    expect(root.querySelector("#gate-form")).not.toBeNull();
    expect(root.querySelector("#gate-pw")).not.toBeNull();
  });

  it("showGate rejects wrong password", async () => {
    // Return hash of "wrong" — doesn't match CORRECT_HASH
    mockDigest.mockResolvedValue(hexToBytes("abcd".padEnd(64, "0")).buffer);

    const { showGate } = await import("../src/site-gate");
    const root = document.getElementById("app")!;
    showGate(root);

    const input = root.querySelector("#gate-pw") as HTMLInputElement;
    const form = root.querySelector("#gate-form") as HTMLFormElement;
    input.value = "wrong";
    form.dispatchEvent(new Event("submit", { cancelable: true }));

    // Wait for async hash
    await new Promise((r) => setTimeout(r, 10));

    const error = root.querySelector("#gate-error") as HTMLElement;
    expect(error.style.display).toBe("block");
    expect(error.textContent).toBe("Incorrect password");
    expect(localStorage.getItem("site_authed")).toBeNull();
  });

  it("showGate accepts correct password and sets localStorage", async () => {
    mockDigest.mockResolvedValue(hexToBytes(CORRECT_HASH).buffer);

    const { showGate } = await import("../src/site-gate");
    const root = document.getElementById("app")!;
    const gatePromise = showGate(root);

    const input = root.querySelector("#gate-pw") as HTMLInputElement;
    const form = root.querySelector("#gate-form") as HTMLFormElement;
    input.value = "CarbonSteps2026!";
    form.dispatchEvent(new Event("submit", { cancelable: true }));

    await gatePromise;

    expect(localStorage.getItem("site_authed")).toBe("1");
  });
});
