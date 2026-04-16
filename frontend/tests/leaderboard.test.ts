/**
 * Tests for leaderboard component utilities.
 */
import { describe, it, expect, afterEach } from "vitest";
import { formatSteps, tierBadgeHtml, avatarHtml, openPhotoModal, closePhotoModal } from "../src/components/leaderboard";

describe("formatSteps", () => {
  it("formats numbers with locale separators", () => {
    const result = formatSteps(10000);
    // Result depends on locale, but should contain "10" and "000"
    expect(result).toContain("10");
    expect(result).toContain("000");
  });

  it("handles zero", () => {
    expect(formatSteps(0)).toBe("0");
  });
});

describe("tierBadgeHtml", () => {
  it("returns high badge HTML", () => {
    const html = tierBadgeHtml("high");
    expect(html).toContain("badge--high");
    expect(html).toContain(">10k steps/day");
  });

  it("returns mid badge HTML", () => {
    const html = tierBadgeHtml("mid");
    expect(html).toContain("badge--mid");
  });

  it("returns low badge HTML", () => {
    const html = tierBadgeHtml("low");
    expect(html).toContain("badge--low");
  });

  it("returns empty string for none tier", () => {
    expect(tierBadgeHtml("none")).toBe("");
  });
});

describe("avatarHtml", () => {
  it("returns clickable button when photo URL provided", () => {
    const html = avatarHtml("/uploads/profile_photos/abc.png", "Test User");
    expect(html).toContain("avatar-img");
    expect(html).toContain("/uploads/profile_photos/abc.png");
    expect(html).toContain("avatar--sm");
    expect(html).toContain("avatar--clickable");
    expect(html).toContain("<button");
    expect(html).toContain('data-photo-url="/uploads/profile_photos/abc.png"');
    expect(html).toContain('data-display-name="Test User"');
  });

  it("returns initials when no photo URL", () => {
    const html = avatarHtml(null, "Test User");
    expect(html).toContain("avatar-initials");
    expect(html).toContain("TU");
    expect(html).toContain("avatar--sm");
    expect(html).not.toContain("avatar--clickable");
  });

  it("returns initials for undefined photo URL", () => {
    const html = avatarHtml(undefined, "Alice");
    expect(html).toContain("avatar-initials");
    expect(html).toContain("A");
  });

  it("handles single-word names", () => {
    const html = avatarHtml(null, "Alice");
    expect(html).toContain("A");
  });
});

describe("openPhotoModal", () => {
  afterEach(() => {
    closePhotoModal();
  });

  it("creates modal overlay in the DOM", () => {
    openPhotoModal("/photo.png", "Alice");
    const overlay = document.querySelector(".photo-modal-overlay");
    expect(overlay).not.toBeNull();
    expect(overlay?.getAttribute("role")).toBe("dialog");
  });

  it("shows full-size photo and display name", () => {
    openPhotoModal("/photo.png", "Alice");
    const img = document.querySelector<HTMLImageElement>(".photo-modal-img");
    expect(img?.src).toContain("/photo.png");
    expect(img?.alt).toBe("Alice");
    expect(document.querySelector(".photo-modal-name")?.textContent).toBe("Alice");
  });

  it("closes on close button click", () => {
    openPhotoModal("/photo.png", "Alice");
    const closeBtn = document.querySelector<HTMLButtonElement>(".photo-modal-close");
    closeBtn?.click();
    expect(document.querySelector(".photo-modal-overlay")).toBeNull();
  });

  it("closes on overlay click", () => {
    const overlay = openPhotoModal("/photo.png", "Alice");
    overlay.click();
    expect(document.querySelector(".photo-modal-overlay")).toBeNull();
  });

  it("closes on Escape key", () => {
    openPhotoModal("/photo.png", "Alice");
    document.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape" }));
    expect(document.querySelector(".photo-modal-overlay")).toBeNull();
  });

  it("replaces existing modal if opened again", () => {
    openPhotoModal("/photo1.png", "Alice");
    openPhotoModal("/photo2.png", "Bob");
    const modals = document.querySelectorAll(".photo-modal-overlay");
    expect(modals.length).toBe(1);
    expect(document.querySelector(".photo-modal-name")?.textContent).toBe("Bob");
  });
});

describe("closePhotoModal", () => {
  it("does nothing when no modal exists", () => {
    expect(() => closePhotoModal()).not.toThrow();
  });
});
