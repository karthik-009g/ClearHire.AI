import { request } from "./client";

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
