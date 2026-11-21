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

function formatErrorDetail(payload) {
  if (!payload) return "";
  if (typeof payload.detail === "string") {
    return payload.detail;
  }
  if (Array.isArray(payload.detail)) {
    return payload.detail
      .map((item) => {
        if (typeof item === "string") return item;
        if (item && typeof item === "object") {
          const loc = Array.isArray(item.loc) ? item.loc.filter((l) => l !== "body").join(".") : "";
          const msg = item.msg || item.message || "Invalid input";
          return loc ? `${loc}: ${msg}` : msg;
        }
        return String(item);
      })
      .join(", ");
  }
  if (typeof payload.detail === "object" && payload.detail !== null) {
    return JSON.stringify(payload.detail);
  }
  if (typeof payload.message === "string") {
    return payload.message;
  }
  return JSON.stringify(payload);
}

async function request(path, options = {}) {
  const headers = {
    ...(options.headers || {}),
  };

  const token = getStoredAuthToken();
  if (token && !headers.Authorization) {
    headers.Authorization = `Bearer ${token}`;
  }

  let res;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers,
    });
  } catch (initialErr) {
    // If calling external API_BASE failed (e.g. browser CORS or direct port block), try relative path via Next.js proxy rewrite
    if (typeof window !== "undefined" && path.startsWith("/api")) {
      try {
        res = await fetch(path, {
          ...options,
          headers,
        });
      } catch {
        throw initialErr;
      }
    } else {
      throw initialErr;
    }
  }

  if (!res.ok) {
    const contentType = res.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
      const payload = await res.json();
      const detail = formatErrorDetail(payload);
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
