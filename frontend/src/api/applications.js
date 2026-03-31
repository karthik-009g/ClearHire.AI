import { request } from "./client";

export async function listApplications() {
  return request("/api/applications/");
}

export async function updateApplicationStatus(applicationId, status, notes = "") {
  return request(`/api/applications/${applicationId}/status`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status, notes }),
  });
}
