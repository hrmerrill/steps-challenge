/**
 * Tests for the profile page (includes log steps form + history).
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
  isAuthenticated: vi.fn(),
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
import { renderProfile } from "../src/pages/profile";

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

describe("profile page", () => {
  let container: HTMLElement;

  beforeEach(() => {
    container = document.createElement("div");
    document.body.innerHTML = "";
    document.body.appendChild(container);
    vi.clearAllMocks();
  });

  it("redirects to login when not authenticated", async () => {
    mockIsAuth.mockReturnValue(false);
    await renderProfile(container);
    expect(mockNavigate).toHaveBeenCalledWith("/login");
  });

  it("shows tier dash placeholder before summary loads", async () => {
    mockIsAuth.mockReturnValue(true);
    mockGetUser.mockReturnValue(TEST_USER);
    mockApiFetch.mockRejectedValue(new Error("network"));

    await renderProfile(container);

    const tierEl = container.querySelector("#profile-tier");
    expect(tierEl).not.toBeNull();
    expect(tierEl!.textContent).toBe("—");
  });

  it("shows high tier for 10k+ avg daily steps", async () => {
    mockIsAuth.mockReturnValue(true);
    mockGetUser.mockReturnValue(TEST_USER);
    mockApiFetch.mockImplementation(async (path: string) => {
      if (path === "/steps/summary") {
        return { total_steps: 300_000, total_miles: 150, days_logged: 30, average_daily: 12_000 };
      }
      if (path === "/leaderboard/overall/my-stats") {
        return {
          user_id: 1, display_name: "Test User", total_steps: 300_000,
          total_miles: 150, rank: 1, total_users: 5, days_logged: 30, average_daily: 12_000,
          miles_club_tier: "high", miles_club_average_daily: 12_000,
        };
      }
      if (path === "/steps/") return [];
      if (path === "/challenges/") return [];
      return [];
    });

    await renderProfile(container);

    const tierEl = container.querySelector("#profile-tier")!;
    expect(tierEl.textContent).toContain(">10k steps/day");
    expect(tierEl.innerHTML).toContain("badge--high");
    expect(tierEl.textContent).toContain("12,000 steps/day");
  });

  it("shows mid tier for 5k-10k avg daily steps", async () => {
    mockIsAuth.mockReturnValue(true);
    mockGetUser.mockReturnValue(TEST_USER);
    mockApiFetch.mockImplementation(async (path: string) => {
      if (path === "/steps/summary") {
        return { total_steps: 150_000, total_miles: 75, days_logged: 30, average_daily: 7_500 };
      }
      if (path === "/leaderboard/overall/my-stats") {
        return {
          user_id: 1, display_name: "Test User", total_steps: 150_000,
          total_miles: 75, rank: 2, total_users: 5, days_logged: 30, average_daily: 7_500,
          miles_club_tier: "mid", miles_club_average_daily: 7_500,
        };
      }
      if (path === "/steps/") return [];
      if (path === "/challenges/") return [];
      return [];
    });

    await renderProfile(container);

    const tierEl = container.querySelector("#profile-tier")!;
    expect(tierEl.innerHTML).toContain("badge--mid");
    expect(tierEl.textContent).toContain("7,500 steps/day");
  });

  it("shows low tier for under 5k avg daily steps", async () => {
    mockIsAuth.mockReturnValue(true);
    mockGetUser.mockReturnValue(TEST_USER);
    mockApiFetch.mockImplementation(async (path: string) => {
      if (path === "/steps/summary") {
        return { total_steps: 30_000, total_miles: 15, days_logged: 30, average_daily: 2_000 };
      }
      if (path === "/leaderboard/overall/my-stats") {
        return {
          user_id: 1, display_name: "Test User", total_steps: 30_000,
          total_miles: 15, rank: 3, total_users: 5, days_logged: 30, average_daily: 2_000,
          miles_club_tier: "low", miles_club_average_daily: 2_000,
        };
      }
      if (path === "/steps/") return [];
      if (path === "/challenges/") return [];
      return [];
    });

    await renderProfile(container);

    const tierEl = container.querySelector("#profile-tier")!;
    expect(tierEl.innerHTML).toContain("badge--low");
    expect(tierEl.textContent).toContain("2,000 steps/day");
  });

  it("renders all-time stats grid with rank", async () => {
    mockIsAuth.mockReturnValue(true);
    mockGetUser.mockReturnValue(TEST_USER);
    mockApiFetch.mockImplementation(async (path: string) => {
      if (path === "/steps/summary") {
        return { total_steps: 300_000, total_miles: 150, days_logged: 30, average_daily: 10_000 };
      }
      if (path === "/leaderboard/overall/my-stats") {
        return {
          user_id: 1, display_name: "Test User", total_steps: 300_000,
          total_miles: 150, rank: 2, total_users: 10, days_logged: 30, average_daily: 10_000,
          miles_club_tier: "high", miles_club_average_daily: 10_000,
        };
      }
      if (path === "/steps/") return [];
      if (path === "/challenges/") return [];
      return [];
    });

    await renderProfile(container);

    expect(container.innerHTML).toContain("300,000");
    expect(container.innerHTML).toContain("Total Steps");
    expect(container.innerHTML).toContain("150");
    expect(container.innerHTML).toContain("Total Miles");
    expect(container.innerHTML).toContain("Avg Daily Steps");
    expect(container.innerHTML).toContain("Rank 2 of 10");
  });

  it("shows active challenge stats when user has joined", async () => {
    mockIsAuth.mockReturnValue(true);
    mockGetUser.mockReturnValue(TEST_USER);
    mockApiFetch.mockImplementation(async (path: string) => {
      if (path === "/steps/summary") {
        return { total_steps: 100_000, total_miles: 50, days_logged: 20, average_daily: 5_000 };
      }
      if (path === "/leaderboard/overall/my-stats") {
        return {
          user_id: 1, display_name: "Test User", total_steps: 100_000,
          total_miles: 50, rank: 1, total_users: 1, days_logged: 20, average_daily: 5_000,
          miles_club_tier: "mid", miles_club_average_daily: 5_000,
        };
      }
      if (path === "/challenges/") {
        return [{
          id: 1, name: "April Challenge", description: null,
          start_date: "2026-04-01", end_date: "2026-04-30",
          is_active: true, participant_count: 3,
        }];
      }
      if (path === "/challenges/1/membership") return { joined: true, miles_club_tier: "mid" };
      if (path === "/challenges/1/my-stats") {
        return {
          user_id: 1, display_name: "Test User", challenge_id: 1,
          total_steps: 50_000, total_miles: 25, rank: 1, total_participants: 3,
          days_logged: 10, average_daily: 5_000, miles_club_tier: "mid",
        };
      }
      if (path === "/steps/") return [];
      if (path.startsWith("/steps/")) return [];
      return [];
    });

    await renderProfile(container);

    expect(container.innerHTML).toContain("Your Stats — April Challenge");
    expect(container.innerHTML).toContain("50,000");
    expect(container.innerHTML).toContain("Rank 1 of 3");
  });

  it("shows initials avatar when no photo uploaded", async () => {
    mockIsAuth.mockReturnValue(true);
    mockGetUser.mockReturnValue({ ...TEST_USER, profile_photo_url: null });
    mockApiFetch.mockRejectedValue(new Error("network"));

    await renderProfile(container);

    const avatar = container.querySelector("#profile-avatar");
    expect(avatar).not.toBeNull();
    expect(avatar!.innerHTML).toContain("avatar-initials");
    expect(avatar!.innerHTML).toContain("TU");
  });

  it("shows photo when profile_photo_url exists", async () => {
    mockIsAuth.mockReturnValue(true);
    mockGetUser.mockReturnValue({ ...TEST_USER, profile_photo_url: "/uploads/profile_photos/abc.png" });
    mockApiFetch.mockRejectedValue(new Error("network"));

    await renderProfile(container);

    const avatar = container.querySelector("#profile-avatar");
    expect(avatar).not.toBeNull();
    expect(avatar!.innerHTML).toContain("avatar-img");
    expect(avatar!.innerHTML).toContain("/uploads/profile_photos/abc.png");
  });

  it("shows upload button when no photo", async () => {
    mockIsAuth.mockReturnValue(true);
    mockGetUser.mockReturnValue({ ...TEST_USER, profile_photo_url: null });
    mockApiFetch.mockRejectedValue(new Error("network"));

    await renderProfile(container);

    expect(container.innerHTML).toContain("Upload Photo");
    expect(container.querySelector("#remove-photo-btn")).toBeNull();
  });

  it("shows change and remove buttons when photo exists", async () => {
    mockIsAuth.mockReturnValue(true);
    mockGetUser.mockReturnValue({ ...TEST_USER, profile_photo_url: "/uploads/profile_photos/abc.png" });
    mockApiFetch.mockRejectedValue(new Error("network"));

    await renderProfile(container);

    expect(container.innerHTML).toContain("Change Photo");
    expect(container.querySelector("#remove-photo-btn")).not.toBeNull();
  });

  // --- Log Steps form (merged into profile) ---

  it("renders log steps form alongside profile", async () => {
    mockIsAuth.mockReturnValue(true);
    mockGetUser.mockReturnValue(TEST_USER);
    mockApiFetch.mockImplementation(async (path: string) => {
      if (path === "/steps/") return [];
      throw new Error("network");
    });

    await renderProfile(container);
    await new Promise((r) => setTimeout(r, 50));

    expect(container.querySelector("#log-form")).not.toBeNull();
    expect(container.innerHTML).toContain("Log Steps");
    expect(container.innerHTML).toContain("Step History");
  });

  it("shows step history in profile page", async () => {
    mockIsAuth.mockReturnValue(true);
    mockGetUser.mockReturnValue(TEST_USER);
    mockApiFetch.mockImplementation(async (path: string) => {
      if (path === "/steps/") {
        return [
          { id: 1, user_id: 1, date: "2026-04-15", step_count: 10000, source: "manual" },
          { id: 2, user_id: 1, date: "2026-04-14", step_count: 8000, source: "manual" },
        ];
      }
      throw new Error("network");
    });

    await renderProfile(container);
    await new Promise((r) => setTimeout(r, 50));

    expect(container.innerHTML).toContain("10,000");
    expect(container.innerHTML).toContain("8,000");
  });

  it("shows edit and delete buttons for manual entries in profile", async () => {
    mockIsAuth.mockReturnValue(true);
    mockGetUser.mockReturnValue(TEST_USER);
    mockApiFetch.mockImplementation(async (path: string) => {
      if (path === "/steps/") {
        return [{ id: 1, user_id: 1, date: "2026-04-15", step_count: 10000, source: "manual" }];
      }
      throw new Error("network");
    });

    await renderProfile(container);
    await new Promise((r) => setTimeout(r, 50));

    expect(container.querySelectorAll(".edit-btn").length).toBe(1);
    expect(container.querySelectorAll(".delete-btn").length).toBe(1);
  });

  it("uses two-column layout", async () => {
    mockIsAuth.mockReturnValue(true);
    mockGetUser.mockReturnValue(TEST_USER);
    mockApiFetch.mockRejectedValue(new Error("network"));

    await renderProfile(container);

    expect(container.querySelector(".profile-columns")).not.toBeNull();
    expect(container.querySelector(".profile-col-left")).not.toBeNull();
    expect(container.querySelector(".profile-col-right")).not.toBeNull();
  });
});
