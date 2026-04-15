/**
 * Tests for the profile page.
 */
import { describe, it, expect, vi, beforeEach } from "vitest";

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

vi.mock("../src/router", () => ({
  navigate: vi.fn(),
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
    mockApiFetch.mockResolvedValue({
      total_steps: 300_000,
      total_miles: 150,
      days_logged: 30,
      average_daily: 12_000,
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
    mockApiFetch.mockResolvedValue({
      total_steps: 150_000,
      total_miles: 75,
      days_logged: 30,
      average_daily: 7_500,
    });

    await renderProfile(container);

    const tierEl = container.querySelector("#profile-tier")!;
    expect(tierEl.innerHTML).toContain("badge--mid");
    expect(tierEl.textContent).toContain("7,500 steps/day");
  });

  it("shows low tier for under 5k avg daily steps", async () => {
    mockIsAuth.mockReturnValue(true);
    mockGetUser.mockReturnValue(TEST_USER);
    mockApiFetch.mockResolvedValue({
      total_steps: 30_000,
      total_miles: 15,
      days_logged: 30,
      average_daily: 2_000,
    });

    await renderProfile(container);

    const tierEl = container.querySelector("#profile-tier")!;
    expect(tierEl.innerHTML).toContain("badge--low");
    expect(tierEl.textContent).toContain("2,000 steps/day");
  });

  it("renders all-time stats grid", async () => {
    mockIsAuth.mockReturnValue(true);
    mockGetUser.mockReturnValue(TEST_USER);
    mockApiFetch.mockResolvedValue({
      total_steps: 300_000,
      total_miles: 150,
      days_logged: 30,
      average_daily: 10_000,
    });

    await renderProfile(container);

    expect(container.innerHTML).toContain("300,000");
    expect(container.innerHTML).toContain("Total Steps");
    expect(container.innerHTML).toContain("150");
    expect(container.innerHTML).toContain("Total Miles");
    expect(container.innerHTML).toContain("Avg Daily Steps");
  });
});
