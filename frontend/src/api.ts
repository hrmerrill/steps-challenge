/**
 * API client — handles requests to the FastAPI backend.
 *
 * In dev, Vite proxies /api → http://localhost:8000.
 * In prod, set API_BASE to the real server URL.
 */

const API_BASE = "/api";

interface RequestOptions {
  method?: string;
  body?: unknown;
  headers?: Record<string, string>;
}

/** Get the stored JWT token. */
export function getToken(): string | null {
  return localStorage.getItem("token");
}

/** Set (or clear) the stored JWT token. */
export function setToken(token: string | null): void {
  if (token) {
    localStorage.setItem("token", token);
  } else {
    localStorage.removeItem("token");
  }
}

/** Make an authenticated API request. Returns parsed JSON. */
export async function apiFetch<T = unknown>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const { method = "GET", body, headers = {} } = options;

  const token = getToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  if (body && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  const resp = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!resp.ok) {
    if (resp.status === 401) {
      setToken(null);
      window.location.hash = "#/login";
    }
    const errorBody = await resp.json().catch(() => ({}));
    throw new ApiError(resp.status, errorBody.detail ?? resp.statusText);
  }

  if (resp.status === 204) {
    return undefined as T;
  }

  return resp.json() as Promise<T>;
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

/** Upload a file via multipart/form-data. Returns parsed JSON. */
export async function apiUpload<T = unknown>(
  path: string,
  file: File,
  fieldName = "file",
): Promise<T> {
  const headers: Record<string, string> = {};
  const token = getToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const form = new FormData();
  form.append(fieldName, file);

  const resp = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers,
    body: form,
  });

  if (!resp.ok) {
    if (resp.status === 401) {
      setToken(null);
      window.location.hash = "#/login";
    }
    const errorBody = await resp.json().catch(() => ({}));
    throw new ApiError(resp.status, errorBody.detail ?? resp.statusText);
  }

  return resp.json() as Promise<T>;
}
