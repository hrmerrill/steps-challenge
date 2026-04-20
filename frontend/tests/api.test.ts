/**
 * Smoke tests for the API client module.
 */
import { describe, it, expect, beforeEach, vi, afterEach } from "vitest";
import { getToken, setToken, apiFetch, apiUpload, ApiError } from "../src/api";

describe("Token management", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("returns null when no token stored", () => {
    expect(getToken()).toBeNull();
  });

  it("stores and retrieves a token", () => {
    setToken("test-jwt-123");
    expect(getToken()).toBe("test-jwt-123");
  });

  it("clears token when set to null", () => {
    setToken("test-jwt-123");
    setToken(null);
    expect(getToken()).toBeNull();
  });
});

describe("ApiError", () => {
  it("has correct status and message", () => {
    const err = new ApiError(401, "Unauthorized");
    expect(err.status).toBe(401);
    expect(err.message).toBe("Unauthorized");
    expect(err.name).toBe("ApiError");
  });

  it("is an instance of Error", () => {
    const err = new ApiError(500, "Server Error");
    expect(err).toBeInstanceOf(Error);
  });
});

describe("apiFetch — 401 handling", () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    localStorage.clear();
    window.location.hash = "";
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
  });

  it("clears token and redirects to login on 401", async () => {
    setToken("expired-token");

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      statusText: "Unauthorized",
      json: () => Promise.resolve({ detail: "Invalid token" }),
    });

    await expect(apiFetch("/auth/me")).rejects.toThrow(ApiError);
    expect(getToken()).toBeNull();
    expect(window.location.hash).toBe("#/login");
  });

  it("does not clear token on non-401 errors", async () => {
    setToken("valid-token");

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      statusText: "Internal Server Error",
      json: () => Promise.resolve({ detail: "Server error" }),
    });

    await expect(apiFetch("/some/path")).rejects.toThrow(ApiError);
    expect(getToken()).toBe("valid-token");
  });
});

describe("apiUpload — 401 handling", () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    localStorage.clear();
    window.location.hash = "";
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
  });

  it("clears token and redirects to login on 401", async () => {
    setToken("expired-token");

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      statusText: "Unauthorized",
      json: () => Promise.resolve({ detail: "Invalid token" }),
    });

    const file = new File(["data"], "test.txt", { type: "text/plain" });
    await expect(apiUpload("/upload", file)).rejects.toThrow(ApiError);
    expect(getToken()).toBeNull();
    expect(window.location.hash).toBe("#/login");
  });
});
