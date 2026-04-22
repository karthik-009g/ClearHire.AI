const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const AUTH_TOKEN_KEY = "clearhire_access_token";

let authTokenCache = null;

function getStoredAuthToken() {
  if (authTokenCache) {
    return authTokenCache;
  }

  if (typeof window === "undefined") {
    return null;
  }

  const value = window.localStorage.getItem(AUTH_TOKEN_KEY);
  if (value) {
    authTokenCache = value;
  }
  return value;
}

function setAuthToken(token) {
  authTokenCache = token || null;
  if (typeof window === "undefined") {
    return;
  }

  if (token) {
    window.localStorage.setItem(AUTH_TOKEN_KEY, token);
  } else {
    window.localStorage.removeItem(AUTH_TOKEN_KEY);
  }
}

function clearAuthToken() {
  setAuthToken(null);
}

async function request(path, options = {}) {
  const headers = {
    ...(options.headers || {}),
  };

  const token = getStoredAuthToken();
  if (token && !headers.Authorization) {
    headers.Authorization = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    const contentType = res.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
      const payload = await res.json();
      const detail = payload?.detail || payload?.message || JSON.stringify(payload);
      throw new Error(detail || `Request failed: ${res.status}`);
    }

    const text = await res.text();
    throw new Error(text || `Request failed: ${res.status}`);
  }

  const contentType = res.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    return res.json();
  }

  return res.text();
}

export { request, API_BASE, AUTH_TOKEN_KEY, getStoredAuthToken, setAuthToken, clearAuthToken };
