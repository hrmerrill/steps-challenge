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
import { getChallengeStatus, daysUntil } from "../src/pages/landing";

const mockApiFetch = vi.mocked(apiFetch);
const mockIsAuth = vi.mocked(isAuthenticated);
const mockGetUser = vi.mocked(getCurrentUser);

const ACTIVE_CHALLENGE = {
  id: 1,
  name: "April 2026",
  start_date: "2026-04-01",
  end_date: "2026-04-30",
  is_active: true,
  participant_count: 3,
};

const FUTURE_CHALLENGE = {
  id: 2,
  name: "May 2026",
  start_date: "2099-05-01",
  end_date: "2099-05-31",
  is_active: true,
  participant_count: 0,
};

const PAST_CHALLENGE = {
  id: 3,
  name: "March 2026",
  start_date: "2020-03-01",
  end_date: "2020-03-31",
  is_active: false,
  participant_count: 5,
};

const TEST_USER = {
  id: 1,
  email: "test@test.com",
  display_name: "Test",
  garmin_connected: false,
  strava_connected: false,
  fitbit_connected: false,
};

describe("getChallengeStatus", () => {
  it("returns 'upcoming' for future start date", () => {
    expect(getChallengeStatus(FUTURE_CHALLENGE)).toBe("upcoming");
  });

  it("returns 'ended' for past end date", () => {
    expect(getChallengeStatus(PAST_CHALLENGE)).toBe("ended");
  });

  it("returns 'active' for current date range", () => {
    expect(getChallengeStatus(ACTIVE_CHALLENGE)).toBe("active");
  });
});

describe("daysUntil", () => {
  it("returns positive for future dates", () => {
    expect(daysUntil("2099-12-31")).toBeGreaterThan(0);
  });

  it("returns negative for past dates", () => {
    expect(daysUntil("2000-01-01")).toBeLessThan(0);
  });
});

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
    mockGetUser.mockReturnValue(TEST_USER);

    mockApiFetch.mockImplementation(async (path: string) => {
      if (path === "/challenges/") return [ACTIVE_CHALLENGE];
      if (path === "/challenges/1/membership") return { joined: false, miles_club_tier: null };
      if (path.startsWith("/leaderboard/")) return [];
      return [];
    });

    const { renderLanding } = await import("../src/pages/landing");
    await renderLanding(container);

    const joinBtn = container.querySelector("#join-btn");
    expect(joinBtn).not.toBeNull();
    expect(joinBtn!.textContent).toBe("Join Challenge");
  });

  it("shows stats card when user has joined with steps", async () => {
    mockIsAuth.mockReturnValue(true);
    mockGetUser.mockReturnValue(TEST_USER);

    mockApiFetch.mockImplementation(async (path: string) => {
      if (path === "/challenges/") return [ACTIVE_CHALLENGE];
      if (path === "/challenges/1/membership") return { joined: true, miles_club_tier: "silver" };
      if (path === "/challenges/1/my-stats") {
        return {
          user_id: 1, display_name: "Test", challenge_id: 1,
          total_steps: 50000, total_miles: 25.0, rank: 2,
          total_participants: 5, days_logged: 10, average_daily: 5000.0,
          miles_club_tier: "silver",
        };
      }
      if (path.startsWith("/leaderboard/")) return [];
      if (path.startsWith("/steps/")) return [];
      return [];
    });

    const { renderLanding } = await import("../src/pages/landing");
    await renderLanding(container);

    expect(container.innerHTML).toContain("Your Stats");
    expect(container.innerHTML).toContain("50,000");
    expect(container.innerHTML).toContain("Rank 2 of 5");
    expect(container.querySelector("#join-btn")).toBeNull();
  });

  it("does not show join banner or stats for unauthenticated users", async () => {
    mockIsAuth.mockReturnValue(false);
    mockGetUser.mockReturnValue(null);

    mockApiFetch.mockImplementation(async (path: string) => {
      if (path === "/challenges/") return [ACTIVE_CHALLENGE];
      if (path.startsWith("/leaderboard/")) return [];
      return [];
    });

    const { renderLanding } = await import("../src/pages/landing");
    await renderLanding(container);

    expect(container.querySelector("#join-btn")).toBeNull();
    expect(container.innerHTML).not.toContain("Your Stats");
  });

  it("shows message when no challenges exist", async () => {
    mockIsAuth.mockReturnValue(false);
    mockGetUser.mockReturnValue(null);

    mockApiFetch.mockImplementation(async (path: string) => {
      if (path === "/challenges/") return [];
      return [];
    });

    const { renderLanding } = await import("../src/pages/landing");
    await renderLanding(container);

    expect(container.innerHTML).toContain("No challenges yet");
  });

  it("shows upcoming status banner for future challenge", async () => {
    mockIsAuth.mockReturnValue(false);
    mockGetUser.mockReturnValue(null);

    mockApiFetch.mockImplementation(async (path: string) => {
      if (path === "/challenges/") return [FUTURE_CHALLENGE];
      if (path.startsWith("/leaderboard/")) return [];
      return [];
    });

    const { renderLanding } = await import("../src/pages/landing");
    await renderLanding(container);

    expect(container.innerHTML).toContain("starts in");
    expect(container.innerHTML).toContain("challenge-status--upcoming");
  });

  it("shows active status banner for current challenge", async () => {
    mockIsAuth.mockReturnValue(false);
    mockGetUser.mockReturnValue(null);

    mockApiFetch.mockImplementation(async (path: string) => {
      if (path === "/challenges/") return [ACTIVE_CHALLENGE];
      if (path.startsWith("/leaderboard/")) return [];
      return [];
    });

    const { renderLanding } = await import("../src/pages/landing");
    await renderLanding(container);

    expect(container.innerHTML).toContain("is underway");
    expect(container.innerHTML).toContain("challenge-status--active");
  });

  it("shows challenge selector dropdown", async () => {
    mockIsAuth.mockReturnValue(false);
    mockGetUser.mockReturnValue(null);

    mockApiFetch.mockImplementation(async (path: string) => {
      if (path === "/challenges/") return [ACTIVE_CHALLENGE, PAST_CHALLENGE];
      if (path.startsWith("/leaderboard/")) return [];
      return [];
    });

    const { renderLanding } = await import("../src/pages/landing");
    await renderLanding(container);

    const select = container.querySelector("#challenge-select") as HTMLSelectElement;
    expect(select).not.toBeNull();
    // Active challenge + past challenge + "Overall Progress" option
    expect(select.options.length).toBe(3);
    expect(select.options[select.options.length - 1].value).toBe("overall");
  });

  it("does not show join banner for ended challenges", async () => {
    mockIsAuth.mockReturnValue(true);
    mockGetUser.mockReturnValue(TEST_USER);

    mockApiFetch.mockImplementation(async (path: string) => {
      if (path === "/challenges/") return [PAST_CHALLENGE];
      if (path.startsWith("/challenges/3/membership")) return { joined: false, miles_club_tier: null };
      if (path.startsWith("/leaderboard/")) return [];
      return [];
    });

    const { renderLanding } = await import("../src/pages/landing");
    await renderLanding(container);

    expect(container.querySelector("#join-btn")).toBeNull();
    expect(container.innerHTML).toContain("has ended");
  });
});
