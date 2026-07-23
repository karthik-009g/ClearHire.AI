import { API_BASE, getStoredAuthToken, request } from "./client";

export async function uploadResume(file) {
  const formData = new FormData();
  formData.append("file", file);

  return request("/api/resumes/upload", {
    method: "POST",
    body: formData,
  });
}

export async function matchResume(payload) {
  return request("/api/resumes/match", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function tailorResume(payload) {
  return request("/api/resumes/tailor", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function downloadTailoredPackage(payload) {
  const token = getStoredAuthToken();
  const response = await fetch(`${API_BASE}/api/resumes/package/tailor`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorPayload = await response.json().catch(() => null);
    throw new Error(errorPayload?.detail || "Could not create apply-ready package.");
  }

  const contentDisposition = response.headers.get("content-disposition") || "";
  const filename = contentDisposition.match(/filename="?([^";]+)"?/)?.[1] || "clearhire_apply_ready.zip";
  return { blob: await response.blob(), filename };
}

export async function listResumeVersions(resumeId) {
  return request(`/api/resumes/${resumeId}/versions`);
}

export async function getResumeDetail(resumeId) {
  return request(`/api/resumes/${resumeId}`);
}

export async function reembedResume(resumeId) {
  return request(`/api/resumes/${resumeId}/reembed`, {
    method: "POST",
  });
}
