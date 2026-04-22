import { request } from "./client";

export async function getPreferences() {
  return request("/api/jobs/preferences");
}

export async function upsertPreferences(payload) {
  return request("/api/jobs/preferences", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function scrapeJobs(payload) {
  return request("/api/jobs/scrape", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}
