import { request } from "./client";

/**
 * Log in a candidate or administrator.
 * Accepts either:
 * - loginUser(email, password)
 * - loginUser({ email, password })
 * - loginUser({ username, password })
 */
export async function loginUser(emailOrPayload, maybePassword) {
  let email = "";
  let password = "";

  if (typeof emailOrPayload === "object" && emailOrPayload !== null) {
    email = emailOrPayload.email || emailOrPayload.username || "";
    password = emailOrPayload.password || "";
  } else {
    email = emailOrPayload || "";
    password = maybePassword || "";
  }

  const cleanEmail = String(email).trim().toLowerCase();
  const cleanPassword = String(password);

  return request("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email: cleanEmail, password: cleanPassword }),
  });
}

/**
 * Register a candidate.
 * Accepts either:
 * - registerUser(email, password, fullName)
 * - registerUser({ email, password, full_name, name })
 */
export async function registerUser(emailOrPayload, maybePassword, maybeFullName) {
  let email = "";
  let password = "";
  let full_name = "";

  if (typeof emailOrPayload === "object" && emailOrPayload !== null) {
    email = emailOrPayload.email || emailOrPayload.username || "";
    password = emailOrPayload.password || "";
    full_name = emailOrPayload.full_name || emailOrPayload.name || "";
  } else {
    email = emailOrPayload || "";
    password = maybePassword || "";
    full_name = maybeFullName || "";
  }

  const cleanEmail = String(email).trim().toLowerCase();
  const cleanPassword = String(password);
  const cleanName = full_name ? String(full_name).trim() : undefined;

  return request("/api/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      email: cleanEmail,
      password: cleanPassword,
      full_name: cleanName || undefined,
    }),
  });
}

export async function getMe() {
  return request("/api/auth/me");
}
