import { config } from "../config/env";

const TOKEN_KEY = "ats.token.v1";

// sessionStorage can be unavailable (private mode, blocked storage); never let that break the app.
const safeStorage = {
  get: (k) => {
    try { return sessionStorage.getItem(k); } catch { return null; }
  },
  set: (k, v) => {
    try { sessionStorage.setItem(k, v); } catch { /* ignore */ }
  },
  remove: (k) => {
    try { sessionStorage.removeItem(k); } catch { /* ignore */ }
  },
};

export const tokenStore = {
  get: () => safeStorage.get(TOKEN_KEY),
  set: (token) => safeStorage.set(TOKEN_KEY, token),
  clear: () => safeStorage.remove(TOKEN_KEY),
};

const REQUEST_TIMEOUT_MS = 120000;

/** Fire-and-forget request that wakes a sleeping API so that the first real call is not slow. */
export function warmUpApi(baseUrl = config.apiBaseUrl) {
  if (!baseUrl) return;
  try {
    fetch(`${baseUrl}/health`, { mode: "no-cors", cache: "no-store" }).catch(() => {});
  } catch {
    /* nothing to do */
  }
}

export class ApiError extends Error {
  constructor(message, status, details) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.details = details;
  }
}

/**
 * Minimal JSON client. Attaches the bearer token, normalises failures to ApiError and understands
 * the { "detail": "..." } / { "message": "..." } error shapes of FastAPI and Express.
 */
export function createApiClient({ baseUrl = config.apiBaseUrl, getToken = tokenStore.get } = {}) {
  async function request(method, path, body) {
    if (!baseUrl) throw new ApiError("API base URL is not configured (set VITE_API_BASE_URL).", 0);

    const headers = { Accept: "application/json" };
    const token = getToken();
    if (token) headers.Authorization = `Bearer ${token}`;
    if (body !== undefined) headers["Content-Type"] = "application/json";

    // The free hosting tier sleeps when idle and can need about a minute to wake up, so allow for that.
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
    let res;
    try {
      res = await fetch(`${baseUrl}${path}`, {
        method,
        headers,
        body: body === undefined ? undefined : JSON.stringify(body),
        signal: controller.signal,
      });
    } catch (err) {
      if (err?.name === "AbortError") {
        throw new ApiError("The server is taking too long to respond. It may be waking up; please try again in a minute.", 0);
      }
      throw new ApiError("Cannot reach the server. Check your connection and try again.", 0);
    } finally {
      clearTimeout(timer);
    }

    const payload = res.status === 204 ? null : await res.json().catch(() => null);
    if (!res.ok) {
      const message = payload?.detail || payload?.message || `Request failed (${res.status}).`;
      throw new ApiError(typeof message === "string" ? message : "Request failed.", res.status, payload);
    }
    return payload;
  }

  return {
    get: (path) => request("GET", path),
    post: (path, body) => request("POST", path, body ?? {}),
    put: (path, body) => request("PUT", path, body ?? {}),
    del: (path) => request("DELETE", path),
  };
}

export const api = createApiClient();
