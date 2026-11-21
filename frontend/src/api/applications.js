import { request } from "./client";

export async function answerScreenerQuestion(payload) {
  return request("/api/applications/answer-screener", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function prepareApplicationAutofill(payload) {
  return request("/api/applications/autofill", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function updateApplicationAutofill(applicationId, autofillPayload, notes) {
  const payload = { autofill_payload: autofillPayload };
  if (notes !== undefined) payload.notes = notes;

  return request(`/api/applications/${applicationId}/autofill`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function listApplications() {
  return request("/api/applications/");
}

export async function createApplication(payload) {
  return request("/api/applications/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function updateApplicationStatus(applicationId, status, notes = "") {
  return request(`/api/applications/${applicationId}/status`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status, notes }),
  });
}

export async function reviewApplication(applicationId, payload = {}) {
  return request(`/api/applications/${applicationId}/review`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      ...payload,
      confirm_fields_reviewed: true,
    }),
  });
}

export async function markApplicationSubmitted(applicationId, applicationUrl = "") {
  return request(`/api/applications/${applicationId}/submit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      application_url: applicationUrl || null,
      confirm_reviewed: true,
      external_confirmation: true,
    }),
  });
}

export async function getBrowserAutofillPlan(applicationId) {
  return request(`/api/applications/${applicationId}/browser-autofill-plan`);
}

export async function getAtsCompatibility(applicationId) {
  return request(`/api/applications/${applicationId}/ats-compatibility`);
}

export async function triggerN8nWorkflow(applicationId, eventType) {
  return request(`/api/applications/${applicationId}/workflow/n8n`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ event_type: eventType }),
  });
}

export async function getGhostingAlerts() {
  return request("/api/applications/ghosting-alerts");
}

export async function generateApplicationOutreach(applicationId) {
  return request(`/api/applications/${applicationId}/outreach`, {
    method: "POST",
  });
}

export async function generateCustomOutreach(payload) {
  return request("/api/applications/outreach", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}
