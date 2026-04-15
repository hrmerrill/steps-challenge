/**
 * Smoke tests for the API client module.
 */
import { describe, it, expect, beforeEach } from "vitest";
import { getToken, setToken, ApiError } from "../src/api";

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
