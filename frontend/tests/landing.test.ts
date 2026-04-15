/**
 * Tests for landing page dashboard features.
 */
import { describe, it, expect, vi, beforeEach } from "vitest";

// Mock api module before importing landing
vi.mock("../src/api", () => ({
  apiFetch: vi.fn(),
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
}));

vi.mock("../src/components/trail-map", () => ({
  renderTrailMap: vi.fn().mockResolvedValue(undefined),
}));

vi.mock("../src/components/step-chart", () => ({
  renderStepChart: vi.fn(),
  DayData: {},
}));

import { apiFetch } from "../src/api";
import { isAuthenticated, getCurrentUser } from "../src/auth";

const mockApiFetch = vi.mocked(apiFetch);
const mockIsAuth = vi.mocked(isAuthenticated);
const mockGetUser = vi.mocked(getCurrentUser);

describe("landing page", () => {
  let container: HTMLElement;

  beforeEach(() => {
    container = document.createElement("div");
    document.body.innerHTML = "";
    document.body.appendChild(container);
    vi.clearAllMocks();
  });

  it("shows join banner when authenticated but not joined", async () => {
    mockIsAuth.mockReturnValue(true);
    mockGetUser.mockReturnValue({
      id: 1,
      email: "test@test.com",
      display_name: "Test",
      garmin_connected: false,
      strava_connected: false,
      fitbit_connected: false,
    });

    mockApiFetch.mockImplementation(async (path: string) => {
      if (path === "/challenges/") {
        return [{ id: 1, name: "April", start_date: "2026-04-01", end_date: "2026-04-30", is_active: true, participant_count: 3 }];
      }
      if (path === "/challenges/1/membership") {
        return { joined: false, miles_club_tier: null };
      }
      if (path.startsWith("/leaderboard/")) {
        return [];
      }
      return [];
    });

    const { renderLanding } = await import("../src/pages/landing");
    await renderLanding(container);

    const joinBtn = container.querySelector("#join-btn");
    expect(joinBtn).not.toBeNull();
    expect(joinBtn!.textContent).toBe("Join Challenge");
    expect(container.innerHTML).toContain("Join the challenge");
  });

  it("shows stats card when user has joined with steps", async () => {
    mockIsAuth.mockReturnValue(true);
    mockGetUser.mockReturnValue({
      id: 1,
      email: "test@test.com",
      display_name: "Test",
      garmin_connected: false,
      strava_connected: false,
      fitbit_connected: false,
    });

    mockApiFetch.mockImplementation(async (path: string) => {
      if (path === "/challenges/") {
        return [{ id: 1, name: "April", start_date: "2026-04-01", end_date: "2026-04-30", is_active: true, participant_count: 3 }];
      }
      if (path === "/challenges/1/membership") {
        return { joined: true, miles_club_tier: "silver" };
      }
      if (path === "/challenges/1/my-stats") {
        return {
          user_id: 1, display_name: "Test", challenge_id: 1,
          total_steps: 50000, total_miles: 25.0, rank: 2,
          total_participants: 5, days_logged: 10, average_daily: 5000.0,
          miles_club_tier: "silver",
        };
      }
      if (path.startsWith("/leaderboard/")) {
        return [];
      }
      if (path.startsWith("/steps/")) {
        return [];
      }
      return [];
    });

    const { renderLanding } = await import("../src/pages/landing");
    await renderLanding(container);

    // Stats card should be visible
    expect(container.innerHTML).toContain("Your Stats");
    expect(container.innerHTML).toContain("50,000");
    expect(container.innerHTML).toContain("Rank 2 of 5");
    expect(container.innerHTML).toContain("25");

    // Join banner should NOT be visible
    const joinBtn = container.querySelector("#join-btn");
    expect(joinBtn).toBeNull();
  });

  it("does not show join banner or stats for unauthenticated users", async () => {
    mockIsAuth.mockReturnValue(false);
    mockGetUser.mockReturnValue(null);

    mockApiFetch.mockImplementation(async (path: string) => {
      if (path === "/challenges/") {
        return [{ id: 1, name: "April", start_date: "2026-04-01", end_date: "2026-04-30", is_active: true, participant_count: 3 }];
      }
      if (path.startsWith("/leaderboard/")) {
        return [];
      }
      return [];
    });

    const { renderLanding } = await import("../src/pages/landing");
    await renderLanding(container);

    expect(container.querySelector("#join-btn")).toBeNull();
    expect(container.innerHTML).not.toContain("Your Stats");
  });

  it("shows message when no active challenge exists", async () => {
    mockIsAuth.mockReturnValue(false);
    mockGetUser.mockReturnValue(null);

    mockApiFetch.mockImplementation(async (path: string) => {
      if (path === "/challenges/") {
        return [{ id: 1, name: "Old", start_date: "2025-01-01", end_date: "2025-01-31", is_active: false, participant_count: 0 }];
      }
      return [];
    });

    const { renderLanding } = await import("../src/pages/landing");
    await renderLanding(container);

    expect(container.innerHTML).toContain("No active challenge");
  });
});
