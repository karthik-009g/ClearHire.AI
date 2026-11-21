import { request } from "./client";

export async function getMorningDigestPreview() {
  return request("/api/digest/preview");
}

export async function sendMorningDigest(payload) {
  return request("/api/digest/send", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function getDigestHistory() {
  return request("/api/digest/history");
}

export async function getFunnelAnalytics() {
  return request("/api/analytics/funnel");
}
