/**
 * Tests for log-steps functionality (now part of profile page) — step history, edit, and delete.
 */
import { describe, it, expect, vi, beforeEach } from "vitest";

vi.mock("../src/api", () => ({
  apiFetch: vi.fn(),
  apiUpload: vi.fn(),
  ApiError: class ApiError extends Error {
    status: number;
    constructor(status: number, message: string) {
      super(message);
      this.status = status;
      this.name = "ApiError";
    }
  },
}));

vi.mock("../src/auth", () => ({
  isAuthenticated: vi.fn().mockReturnValue(true),
  getCurrentUser: vi.fn(),
  fetchMe: vi.fn(),
}));

vi.mock("../src/router", () => ({
  navigate: vi.fn(),
}));

vi.mock("../src/components/step-chart", () => ({
  renderStepChart: vi.fn(),
  DayData: {},
}));

import { apiFetch } from "../src/api";
import { isAuthenticated, getCurrentUser } from "../src/auth";
import { navigate } from "../src/router";

const mockApiFetch = vi.mocked(apiFetch);
const mockIsAuth = vi.mocked(isAuthenticated);
const mockGetUser = vi.mocked(getCurrentUser);
const mockNavigate = vi.mocked(navigate);

const TEST_USER = {
  id: 1,
  email: "test@example.com",
  display_name: "Test User",
  profile_photo_url: null as string | null,
  garmin_connected: false,
  strava_connected: false,
  fitbit_connected: false,
};

describe("log-steps (in profile page)", () => {
  let container: HTMLElement;

  beforeEach(() => {
    container = document.createElement("div");
    document.body.innerHTML = "";
    document.body.appendChild(container);
    vi.clearAllMocks();
    mockIsAuth.mockReturnValue(true);
    mockGetUser.mockReturnValue(TEST_USER);
  });

  it("renders form and step history section", async () => {
    mockApiFetch.mockImplementation(async (path: string) => {
      if (path === "/steps/") {
        return [
          { id: 1, user_id: 1, date: "2026-04-15", step_count: 10000, source: "manual" },
          { id: 2, user_id: 1, date: "2026-04-14", step_count: 8000, source: "manual" },
        ];
      }
      throw new Error("network");
    });

    const { renderProfile } = await import("../src/pages/profile");
    await renderProfile(container);
    await new Promise((r) => setTimeout(r, 50));

    expect(container.querySelector("#log-form")).not.toBeNull();
    expect(container.innerHTML).toContain("Step History");
    expect(container.innerHTML).toContain("10,000");
    expect(container.innerHTML).toContain("8,000");
  });

  it("shows edit and delete buttons for manual entries", async () => {
    mockApiFetch.mockImplementation(async (path: string) => {
      if (path === "/steps/") {
        return [{ id: 1, user_id: 1, date: "2026-04-15", step_count: 10000, source: "manual" }];
      }
      throw new Error("network");
    });

    const { renderProfile } = await import("../src/pages/profile");
    await renderProfile(container);
    await new Promise((r) => setTimeout(r, 50));

    const editBtns = container.querySelectorAll(".edit-btn");
    const deleteBtns = container.querySelectorAll(".delete-btn");
    expect(editBtns.length).toBe(1);
    expect(deleteBtns.length).toBe(1);
  });

  it("does not show edit button for non-manual entries", async () => {
    mockApiFetch.mockImplementation(async (path: string) => {
      if (path === "/steps/") {
        return [{ id: 1, user_id: 1, date: "2026-04-15", step_count: 10000, source: "garmin" }];
      }
      throw new Error("network");
    });

    const { renderProfile } = await import("../src/pages/profile");
    await renderProfile(container);
    await new Promise((r) => setTimeout(r, 50));

    expect(container.querySelectorAll(".edit-btn").length).toBe(0);
    expect(container.querySelectorAll(".delete-btn").length).toBe(1);
  });

  it("populates form when edit is clicked", async () => {
    mockApiFetch.mockImplementation(async (path: string) => {
      if (path === "/steps/") {
        return [{ id: 1, user_id: 1, date: "2026-04-15", step_count: 10000, source: "manual" }];
      }
      throw new Error("network");
    });

    const { renderProfile } = await import("../src/pages/profile");
    await renderProfile(container);
    await new Promise((r) => setTimeout(r, 50));

    const editBtn = container.querySelector(".edit-btn") as HTMLButtonElement;
    editBtn.click();

    const dateInput = container.querySelector("#step-date") as HTMLInputElement;
    const countInput = container.querySelector("#step-count") as HTMLInputElement;
    const submitBtn = container.querySelector("#log-submit-btn") as HTMLButtonElement;

    expect(dateInput.value).toBe("2026-04-15");
    expect(countInput.value).toBe("10000");
    expect(submitBtn.textContent).toBe("Update Steps");
    expect(dateInput.readOnly).toBe(true);
  });

  it("shows cancel button when editing", async () => {
    mockApiFetch.mockImplementation(async (path: string) => {
      if (path === "/steps/") {
        return [{ id: 1, user_id: 1, date: "2026-04-15", step_count: 10000, source: "manual" }];
      }
      throw new Error("network");
    });

    const { renderProfile } = await import("../src/pages/profile");
    await renderProfile(container);
    await new Promise((r) => setTimeout(r, 50));

    const editBtn = container.querySelector(".edit-btn") as HTMLButtonElement;
    editBtn.click();

    const cancelBtn = container.querySelector("#cancel-edit-btn") as HTMLButtonElement;
    expect(cancelBtn.style.display).toBe("block");
  });

  it("shows empty history message when no entries", async () => {
    mockApiFetch.mockImplementation(async (path: string) => {
      if (path === "/steps/") return [];
      throw new Error("network");
    });

    const { renderProfile } = await import("../src/pages/profile");
    await renderProfile(container);
    await new Promise((r) => setTimeout(r, 50));

    expect(container.innerHTML).toContain("No steps logged yet");
  });

  it("redirects to login when not authenticated", async () => {
    mockIsAuth.mockReturnValue(false);

    const { renderProfile } = await import("../src/pages/profile");
    await renderProfile(container);

    expect(mockNavigate).toHaveBeenCalledWith("/login");
  });
});
