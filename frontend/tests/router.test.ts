/**
 * Tests for the client-side router.
 */
import { describe, it, expect, beforeEach } from "vitest";
import { addRoute, currentRoute, navigate } from "../src/router";

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

  it("navigate sets the hash", () => {
    navigate("/register");
    expect(window.location.hash).toBe("#/register");
  });
});
