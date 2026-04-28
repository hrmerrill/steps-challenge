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
  name: "Carbon Miles Challenge - May",
  description: "Walk your way through May!",
  start_date: "2026-04-01",
  end_date: "2026-04-30",
  is_active: true,
  participant_count: 3,
};

const FUTURE_CHALLENGE = {
  id: 2,
  name: "June Challenge",
  description: null,
  start_date: "2099-05-01",
  end_date: "2099-05-31",
  is_active: true,
  participant_count: 0,
};

const PAST_CHALLENGE = {
  id: 3,
  name: "March 2026",
  description: null,
  start_date: "2020-03-01",
  end_date: "2020-03-31",
  is_active: false,
  participant_count: 5,
};

const TEST_USER = {
  id: 1,
  email: "test@test.com",
  display_name: "Test",
  profile_photo_url: null,
  preferred_step_source: "manual",
  garmin_connected: false,
  strava_connected: false,
  google_health_connected: false,
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
      if (path === "/challenges/1/team-stats") {
        return {
          challenge_id: 1, total_steps: 0, total_miles: 0,
          total_participants: 0, total_days_logged: 0,
          average_daily_per_participant: 0,
        };
      }
      if (path.startsWith("/leaderboard/")) return [];
      return [];
    });

    const { renderLanding } = await import("../src/pages/landing");
    await renderLanding(container);

    const joinBtn = container.querySelector("#join-btn");
    expect(joinBtn).not.toBeNull();
    expect(joinBtn!.textContent).toBe("Join Challenge");
  });

  it("shows team stats card for challenge (no auth required)", async () => {
    mockIsAuth.mockReturnValue(false);
    mockGetUser.mockReturnValue(null);

    mockApiFetch.mockImplementation(async (path: string) => {
      if (path === "/challenges/") return [ACTIVE_CHALLENGE];
      if (path === "/challenges/1/team-stats") {
        return {
          challenge_id: 1, total_steps: 150000, total_miles: 75.0,
          total_participants: 5, total_days_logged: 30,
          average_daily_per_participant: 5000.0,
        };
      }
      if (path.startsWith("/leaderboard/")) return [];
      return [];
    });

    const { renderLanding } = await import("../src/pages/landing");
    await renderLanding(container);

    expect(container.innerHTML).toContain("Team Stats");
    expect(container.innerHTML).toContain("150,000");
    expect(container.innerHTML).toContain("5 participants");
    expect(container.innerHTML).not.toContain("Your Stats");
  });

  it("does not show join banner for unauthenticated users but shows team stats", async () => {
    mockIsAuth.mockReturnValue(false);
    mockGetUser.mockReturnValue(null);

    mockApiFetch.mockImplementation(async (path: string) => {
      if (path === "/challenges/") return [ACTIVE_CHALLENGE];
      if (path === "/challenges/1/team-stats") {
        return {
          challenge_id: 1, total_steps: 100000, total_miles: 50.0,
          total_participants: 3, total_days_logged: 15,
          average_daily_per_participant: 6666.7,
        };
      }
      if (path.startsWith("/leaderboard/")) return [];
      return [];
    });

    const { renderLanding } = await import("../src/pages/landing");
    await renderLanding(container);

    expect(container.querySelector("#join-btn")).toBeNull();
    expect(container.innerHTML).not.toContain("Your Stats");
    expect(container.innerHTML).toContain("Team Stats");
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
      if (path.includes("/team-stats")) {
        return {
          challenge_id: 2, total_steps: 0, total_miles: 0,
          total_participants: 0, total_days_logged: 0,
          average_daily_per_participant: 0,
        };
      }
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
      if (path.includes("/team-stats")) {
        return {
          challenge_id: 1, total_steps: 0, total_miles: 0,
          total_participants: 0, total_days_logged: 0,
          average_daily_per_participant: 0,
        };
      }
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
      if (path.includes("/team-stats")) {
        return {
          challenge_id: 1, total_steps: 0, total_miles: 0,
          total_participants: 0, total_days_logged: 0,
          average_daily_per_participant: 0,
        };
      }
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
      if (path === "/challenges/3/team-stats") {
        return {
          challenge_id: 3, total_steps: 0, total_miles: 0,
          total_participants: 0, total_days_logged: 0,
          average_daily_per_participant: 0,
        };
      }
      if (path.startsWith("/leaderboard/")) return [];
      return [];
    });

    const { renderLanding } = await import("../src/pages/landing");
    await renderLanding(container);

    expect(container.querySelector("#join-btn")).toBeNull();
    expect(container.innerHTML).toContain("has ended");
  });

  it("shows How It Works button in status banner", async () => {
    mockIsAuth.mockReturnValue(false);
    mockGetUser.mockReturnValue(null);

    mockApiFetch.mockImplementation(async (path: string) => {
      if (path === "/challenges/") return [ACTIVE_CHALLENGE];
      if (path.includes("/team-stats")) {
        return {
          challenge_id: 1, total_steps: 0, total_miles: 0,
          total_participants: 0, total_days_logged: 0,
          average_daily_per_participant: 0,
        };
      }
      if (path.startsWith("/leaderboard/")) return [];
      return [];
    });

    const { renderLanding } = await import("../src/pages/landing");
    await renderLanding(container);

    const btn = container.querySelector("#how-it-works-btn");
    expect(btn).not.toBeNull();
    expect(btn!.textContent).toContain("How It Works");
  });

  it("toggles How It Works card on click", async () => {
    mockIsAuth.mockReturnValue(false);
    mockGetUser.mockReturnValue(null);

    mockApiFetch.mockImplementation(async (path: string) => {
      if (path === "/challenges/") return [ACTIVE_CHALLENGE];
      if (path.includes("/team-stats")) {
        return {
          challenge_id: 1, total_steps: 0, total_miles: 0,
          total_participants: 0, total_days_logged: 0,
          average_daily_per_participant: 0,
        };
      }
      if (path.startsWith("/leaderboard/")) return [];
      return [];
    });

    const { renderLanding } = await import("../src/pages/landing");
    await renderLanding(container);

    const card = container.querySelector("#how-it-works-card") as HTMLElement;
    expect(card.style.display).toBe("none");

    // Click to open
    container.querySelector<HTMLElement>("#how-it-works-btn")!.click();
    expect(card.style.display).toBe("block");

    // Click close to hide
    container.querySelector<HTMLElement>("#how-it-works-close")!.click();
    expect(card.style.display).toBe("none");
  });

  it("shows challenge description in How It Works card", async () => {
    mockIsAuth.mockReturnValue(false);
    mockGetUser.mockReturnValue(null);

    mockApiFetch.mockImplementation(async (path: string) => {
      if (path === "/challenges/") return [ACTIVE_CHALLENGE];
      if (path.includes("/team-stats")) {
        return {
          challenge_id: 1, total_steps: 0, total_miles: 0,
          total_participants: 0, total_days_logged: 0,
          average_daily_per_participant: 0,
        };
      }
      if (path.startsWith("/leaderboard/")) return [];
      return [];
    });

    const { renderLanding } = await import("../src/pages/landing");
    await renderLanding(container);

    const card = container.querySelector("#how-it-works-card") as HTMLElement;
    expect(card.innerHTML).toContain("Walk your way through May!");
    expect(card.innerHTML).toContain("Miles Clubs");
    expect(card.innerHTML).toContain("Virtual Trail Map");
    expect(card.innerHTML).toContain("Leaderboard");
    expect(card.innerHTML).toContain("10,000+");
  });
});
