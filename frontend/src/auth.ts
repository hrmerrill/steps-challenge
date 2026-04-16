/**
 * Auth state management — login, logout, token storage.
 */

import { apiFetch, setToken, getToken } from "./api";

export interface AuthUser {
  id: number;
  email: string;
  display_name: string;
  profile_photo_url: string | null;
  garmin_connected: boolean;
  strava_connected: boolean;
  fitbit_connected: boolean;
}

let currentUser: AuthUser | null = null;

/** Check if user is currently authenticated. */
export function isAuthenticated(): boolean {
  return getToken() !== null;
}

/** Get the current user (cached). */
export function getCurrentUser(): AuthUser | null {
  return currentUser;
}

/** Register a new account. */
export async function register(
  email: string,
  password: string,
  displayName: string,
): Promise<AuthUser> {
  const resp = await apiFetch<{ access_token: string }>("/auth/register", {
    method: "POST",
    body: { email, password, display_name: displayName },
  });
  setToken(resp.access_token);
  return fetchMe();
}

/** Log in with email and password. */
export async function login(
  email: string,
  password: string,
): Promise<AuthUser> {
  const resp = await apiFetch<{ access_token: string }>("/auth/login", {
    method: "POST",
    body: { email, password },
  });
  setToken(resp.access_token);
  return fetchMe();
}

/** Log out — clear token and cached user. */
export function logout(): void {
  setToken(null);
  currentUser = null;
}

/** Fetch the current user profile from the API. */
export async function fetchMe(): Promise<AuthUser> {
  currentUser = await apiFetch<AuthUser>("/auth/me");
  return currentUser;
}
