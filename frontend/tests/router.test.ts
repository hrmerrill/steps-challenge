/**
 * Tests for the client-side router.
 */
import { describe, it, expect, beforeEach } from "vitest";
import { currentRoute, navigate } from "../src/router";

describe("Router", () => {
  beforeEach(() => {
    window.location.hash = "";
  });

  it("returns / when hash is empty", () => {
    expect(currentRoute()).toBe("/");
  });

  it("returns route from hash", () => {
    window.location.hash = "#/login";
    expect(currentRoute()).toBe("/login");
  });

  it("strips query parameters from hash", () => {
    window.location.hash = "#/profile?google_health=connected";
    expect(currentRoute()).toBe("/profile");
  });

  it("handles hash with multiple query parameters", () => {
    window.location.hash = "#/profile?a=1&b=2";
    expect(currentRoute()).toBe("/profile");
  });

  it("navigate sets the hash", () => {
    navigate("/register");
    expect(window.location.hash).toBe("#/register");
  });
});
