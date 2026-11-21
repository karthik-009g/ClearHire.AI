import { useCallback, useEffect, useMemo, useState } from "react";
import ModuleLayout from "../components/ModuleLayout";
import {
  createApplication,
  generateApplicationOutreach,
  getAtsCompatibility,
  getBrowserAutofillPlan,
  getGhostingAlerts,
  listApplications,
  markApplicationSubmitted,
  reviewApplication,
  triggerN8nWorkflow,
  updateApplicationStatus,
} from "../api/applications";
import { listResumeVersions } from "../api/resumes";
import { getJdContext, getResmatContext } from "../lib/moduleState";

function formatDate(value) {
  if (!value) {
    return "Not available";
  }

  return new Date(value).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

const KANBAN_STAGES = [
  { id: "saved", title: "📌 Saved & Draft", statuses: ["bookmarked", "draft"], color: "#5369d9" },
  { id: "prep", title: "📝 Review & Prep", statuses: ["pending", "review_required", "reviewed"], color: "#bd7652" },
  { id: "applied", title: "🚀 Submitted", statuses: ["applied"], color: "#15803d" },
  { id: "screening", title: "📞 Recruiter Screen", statuses: ["screening"], color: "#8d9cf2" },
  { id: "interviewing", title: "💻 Interview Round", statuses: ["interviewing"], color: "#4052b3" },
  { id: "offer", title: "🏆 Offer Received", statuses: ["offer"], color: "#166534" },
  { id: "ghosted", title: "👻 Ghosted / Archived", statuses: ["ghosted", "rejected"], color: "#985b39" },
];

export default function ApplicationsPage() {
  const [resumeContext] = useState(() => getResmatContext());
  const [jdContext] = useState(() => getJdContext());
  const [versions, setVersions] = useState([]);
  const [selectedVersionId, setSelectedVersionId] = useState("");
  const [status, setStatus] = useState("pending");
  const [applicationUrl, setApplicationUrl] = useState("");
  const [notes, setNotes] = useState("");
  const [applications, setApplications] = useState([]);
  const [filterQuery, setFilterQuery] = useState("");
  const [ghostingAlerts, setGhostingAlerts] = useState(null);
  const [activeView, setActiveView] = useState("kanban"); // "kanban" | "table"
  const [showAlternatives, setShowAlternatives] = useState(false);
  const [outreachModal, setOutreachModal] = useState({
    open: false,
    applicationId: null,
    data: null,
    loading: false,
    activeTab: "inmail",
    copied: false,
  });

  const [browserPlan, setBrowserPlan] = useState(null);
  const [atsCompatibility, setAtsCompatibility] = useState(null);
  const [workflowResult, setWorkflowResult] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");

  const jobDescriptionId = jdContext?.match?.job_description_id;
  const targetLabel = useMemo(() => {
    if (!jdContext?.roleTitle) {
      return "Run JD Analyzer to select a job description.";
    }

    return `${jdContext.roleTitle}${jdContext.companyName ? ` at ${jdContext.companyName}` : ""}`;
  }, [jdContext]);

  const filteredApps = useMemo(() => {
    if (!filterQuery.trim()) return applications;
    const q = filterQuery.toLowerCase();
    return applications.filter(
      (a) =>
        (a.job_title || "").toLowerCase().includes(q) ||
        (a.job_company || "").toLowerCase().includes(q) ||
        (a.status || "").toLowerCase().includes(q)
    );
  }, [applications, filterQuery]);

  const loadData = useCallback(async () => {
    try {
      const [apps, alerts] = await Promise.all([
        listApplications(),
        getGhostingAlerts().catch(() => null),
      ]);
      setApplications(apps || []);
      if (alerts) {
        setGhostingAlerts(alerts);
      }
    } catch (err) {
      setError(err.message || "Could not load application pipeline.");
    }
  }, []);

  useEffect(() => {
    const resume = resumeContext;

    const load = async () => {
      try {
        await loadData();
        if (!resume?.resumeId) {
          return;
        }

        const payload = await listResumeVersions(resume.resumeId);
        const nextVersions = payload.versions || [];
        setVersions(nextVersions);
        const latest = nextVersions[nextVersions.length - 1];
        setSelectedVersionId(latest ? String(latest.id) : "");
      } catch (err) {
        setError(err.message || "Could not load application tracking data.");
      }
    };

    load();
  }, [loadData, resumeContext]);

  const onCreate = async () => {
    if (!jobDescriptionId) {
      setError("Run JD Analyzer again to create a tracked job description.");
      return;
    }

    if (!selectedVersionId) {
      setError("Upload a resume before creating an application record.");
      return;
    }

    setBusy(true);
    setError("");
    setInfo("");
    try {
      await createApplication({
        job_description_id: jobDescriptionId,
        resume_version_id: Number(selectedVersionId),
        status,
        application_url: applicationUrl.trim() || null,
        notes: notes.trim() || null,
      });
      setApplicationUrl("");
      setNotes("");
      await loadData();
      setInfo("Application record created in pipeline.");
    } catch (err) {
      setError(err.message || "Could not create application record.");
    } finally {
      setBusy(false);
    }
  };

  const onStatusChange = async (applicationId, nextStatus) => {
    setError("");
    try {
      const current = applications.find((a) => a.id === applicationId);
      await updateApplicationStatus(applicationId, nextStatus, current?.notes || "");
      await loadData();
    } catch (err) {
      setError(err.message || "Could not update application status.");
    }
  };

  const onReviewApplication = async (applicationId) => {
    setError("");
    setInfo("");
    try {
      const current = applications.find((a) => a.id === applicationId);
      await reviewApplication(applicationId, {
        autofill_payload: current?.autofill_payload || null,
        notes: current?.notes || "",
      });
      await loadData();
      setInfo("Application fields marked reviewed.");
    } catch (err) {
      setError(err.message || "Could not review application fields.");
    }
  };

  const onMarkSubmitted = async (applicationId) => {
    if (!window.confirm("Have you submitted this application on the employer's portal? ClearHire will record this confirmation.")) {
      return;
    }
    setError("");
    setInfo("");
    try {
      const current = applications.find((a) => a.id === applicationId);
      await markApplicationSubmitted(applicationId, current?.application_url || "");
      await loadData();
      setInfo("Application recorded as submitted based on your confirmation. ClearHire cannot verify the employer portal.");
    } catch (err) {
      setError(err.message || "Could not mark application submitted.");
    }
  };

  const onOpenOutreach = async (applicationId) => {
    setError("");
    setOutreachModal({
      open: true,
      applicationId,
      data: null,
      loading: true,
      activeTab: "inmail",
      copied: false,
    });
    try {
      const data = await generateApplicationOutreach(applicationId);
      setOutreachModal((prev) => ({ ...prev, data, loading: false }));
    } catch (err) {
      setError(err.message || "Could not generate recruiter outreach.");
      setOutreachModal((prev) => ({ ...prev, loading: false }));
    }
  };

  const onCopyOutreachText = (text) => {
    if (!text) return;
    navigator.clipboard.writeText(text);
    setOutreachModal((prev) => ({ ...prev, copied: true }));
    setTimeout(() => {
      setOutreachModal((prev) => ({ ...prev, copied: false }));
    }, 2000);
  };

  const onLoadBrowserPlan = async (applicationId) => {
    setError("");
    setInfo("");
    try {
      const payload = await getBrowserAutofillPlan(applicationId);
      setBrowserPlan(payload.browser_autofill_plan);
      setInfo("Browser autofill plan loaded for reviewed fields.");
    } catch (err) {
      setError(err.message || "Could not load browser autofill plan.");
    }
  };

  const onCheckAts = async (applicationId) => {
    setError("");
    setInfo("");
    try {
      const payload = await getAtsCompatibility(applicationId);
      setAtsCompatibility(payload.ats_compatibility);
      setInfo("ATS compatibility checked.");
    } catch (err) {
      setError(err.message || "Could not check ATS compatibility.");
    }
  };

  const onTriggerWorkflow = async (applicationId, eventType) => {
    setError("");
    setInfo("");
    try {
      const payload = await triggerN8nWorkflow(applicationId, eventType);
      setWorkflowResult(payload.workflow);
      setInfo("n8n workflow payload prepared.");
    } catch (err) {
      setError(err.message || "Could not prepare n8n workflow.");
    }
  };

  return (
    <ModuleLayout
      title="Application Pipeline CRM"
      subtitle="Track saved roles, preparation, applications, interviews, and follow-ups in one candidate-owned pipeline."
    >
      {/* 1. Application no-update reminders */}
      {ghostingAlerts && (
        <article
          className="mp-card"
          style={{
            background: ghostingAlerts.ghosted_count > 0 ? "rgba(254, 242, 242, 0.85)" : "rgba(240, 253, 244, 0.85)",
            backdropFilter: "blur(20px)",
            WebkitBackdropFilter: "blur(20px)",
            border: ghostingAlerts.ghosted_count > 0 ? "1px solid rgba(189, 118, 82, 0.35)" : "1px solid rgba(91, 127, 106, 0.35)",
            borderRadius: "16px",
            boxShadow: "0 4px 16px rgba(36, 35, 31, 0.04)",
            marginBottom: "20px",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px" }}>
            <div>
              <span style={{ fontSize: "12px", textTransform: "uppercase", letterSpacing: "1px", color: ghostingAlerts.ghosted_count > 0 ? "#bd7652" : "#5b7f6a", fontWeight: 700 }}>
                {ghostingAlerts.ghosted_count > 0 ? "⚠️ Follow-up reminder" : "🟢 No overdue follow-ups"}
              </span>
              <h3 style={{ margin: "4px 0" }}>
                {ghostingAlerts.ghosted_count} of {ghostingAlerts.applied_count} submitted or later-stage records have had no update for 14+ days
              </h3>
              <p style={{ margin: 0, fontSize: "14px", color: "var(--text-soft)" }}>
                No-update share of submitted records: <strong>{ghostingAlerts.ghosting_rate_percent}%</strong> | Total tracked records: {ghostingAlerts.total_applications}
              </p>
            </div>
            {ghostingAlerts.recommended_alternatives?.length > 0 && (
              <button
                type="button"
                onClick={() => setShowAlternatives(!showAlternatives)}
                style={{
                  background: "var(--brand)",
                  border: "none",
                  padding: "10px 18px",
                  borderRadius: "999px",
                  color: "#ffffff",
                  fontWeight: 600,
                  cursor: "pointer",
                }}
              >
                {showAlternatives ? "Hide public openings" : "✨ View recent public ATS openings"}
              </button>
            )}
          </div>

          {/* Recent public ATS listings. Availability must be confirmed on the employer site. */}
          {showAlternatives && ghostingAlerts.recommended_alternatives && (
            <div style={{ marginTop: "18px", paddingTop: "14px", borderTop: "1px solid var(--line)" }}>
              <h4 style={{ margin: "0 0 10px 0", color: "#15803d" }}>
                Public ATS listings · confirm availability on the employer site
              </h4>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: "12px" }}>
                {ghostingAlerts.recommended_alternatives.map((alt, i) => (
                  <div
                    key={i}
                    style={{
                      padding: "12px",
                      background: "#ffffff",
                      borderRadius: "12px",
                      border: "1px solid rgba(36, 35, 31, 0.1)",
                      boxShadow: "0 2px 6px rgba(36, 35, 31, 0.03)",
                    }}
                  >
                    <div style={{ fontWeight: 600, fontSize: "15px" }}>{alt.title}</div>
                    <div style={{ fontSize: "13px", color: "var(--text-soft)", margin: "3px 0" }}>
                      {alt.company} • {alt.location || "India"}
                    </div>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "8px" }}>
                      <span style={{ fontSize: "11px", color: "#5b7f6a", background: "rgba(91, 127, 106, 0.12)", padding: "2px 6px", borderRadius: "4px" }}>
                        {alt.ats_type || alt.source || "Public ATS"}
                      </span>
                      <a
                        href={alt.url}
                        target="_blank"
                        rel="noreferrer"
                        style={{ fontSize: "12px", color: "var(--brand)", fontWeight: 600, textDecoration: "none" }}
                      >
                        Open employer posting ➔
                      </a>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </article>
      )}

      {/* 2. Top View Controls & Search Filter */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px", flexWrap: "wrap", gap: "10px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
          <button
            type="button"
            onClick={() => setActiveView("kanban")}
            style={{
              padding: "6px 14px",
              borderRadius: "8px",
              background: activeView === "kanban" ? "var(--brand)" : "rgba(255, 255, 255, 0.7)",
              color: activeView === "kanban" ? "#ffffff" : "var(--ink)",
              boxShadow: activeView === "kanban" ? "0 2px 8px rgba(83, 105, 217, 0.25)" : "none",
              border: "1px solid var(--line)",
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            📋 Kanban Pipeline
          </button>
          <button
            type="button"
            onClick={() => setActiveView("table")}
            style={{
              padding: "6px 14px",
              borderRadius: "8px",
              background: activeView === "table" ? "var(--brand)" : "rgba(255, 255, 255, 0.7)",
              color: activeView === "table" ? "#ffffff" : "var(--ink)",
              boxShadow: activeView === "table" ? "0 2px 8px rgba(83, 105, 217, 0.25)" : "none",
              border: "1px solid var(--line)",
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            📑 Table Details & Actions
          </button>

          {/* Quick Search Filter Input */}
          <div style={{ display: "flex", alignItems: "center", gap: "6px", background: "#ffffff", padding: "4px 10px", borderRadius: "8px", border: "1px solid var(--line)" }}>
            <span style={{ fontSize: "12px", opacity: 0.6 }}>🔍</span>
            <input
              type="text"
              value={filterQuery}
              onChange={(e) => setFilterQuery(e.target.value)}
              placeholder="Filter company or role..."
              style={{ border: "none", outline: "none", fontSize: "12px", fontFamily: "var(--mono)", background: "transparent", width: "160px" }}
            />
            {filterQuery && (
              <button
                type="button"
                onClick={() => setFilterQuery("")}
                style={{ border: "none", background: "none", cursor: "pointer", fontSize: "10px", color: "var(--text-soft)" }}
              >
                ✕
              </button>
            )}
          </div>
        </div>
        <span style={{ fontSize: "13px", color: "var(--text-soft)", fontFamily: "var(--mono)" }}>
          {filteredApps.length} of {applications.length} applications shown
        </span>
      </div>

      {/* 3. Visual Kanban CRM Pipeline */}
      {activeView === "kanban" && (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))",
            gap: "14px",
            alignItems: "flex-start",
            marginBottom: "30px",
          }}
        >
          {KANBAN_STAGES.map((stage) => {
            const stageApps = filteredApps.filter((a) => stage.statuses.includes(a.status));
            return (
              <div
                key={stage.id}
                className="rounded-2xl p-6 bg-[#faf7f0]/85 backdrop-blur-xl border border-[#24231f]/12 shadow-sm flex flex-col gap-2.5 min-h-[400px]"
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: `2px solid ${stage.color}`, paddingBottom: "6px" }}>
                  <span style={{ fontWeight: 700, fontSize: "14px", color: stage.color }}>{stage.title}</span>
                  <span style={{ fontSize: "11px", background: "#eee9df", color: "#24231f", padding: "2px 8px", borderRadius: "999px", fontFamily: "var(--mono)", fontWeight: 600 }}>
                    {stageApps.length}
                  </span>
                </div>

                <div style={{ display: "flex", flexDirection: "column", gap: "10px", flex: 1 }}>
                  {stageApps.map((app) => (
                    <div
                      key={app.id}
                      style={{
                        background: "rgba(255, 255, 255, 0.80)",
                        backdropFilter: "blur(12px)",
                        WebkitBackdropFilter: "blur(12px)",
                        border: app.is_ghosted ? "1px solid #bd7652" : "1px solid rgba(36, 35, 31, 0.09)",
                        borderRadius: "12px",
                        padding: "12px 14px",
                        boxShadow: "0 2px 8px rgba(36, 35, 31, 0.04)",
                        display: "flex",
                        flexDirection: "column",
                        gap: "8px",
                      }}
                    >
                      {/* Company & Role Header */}
                      <div>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "6px" }}>
                          <span style={{ fontWeight: 600, fontSize: "14px", color: "var(--ink)", lineHeight: 1.3 }}>
                            {app.job_title || `Job #${app.job_description_id}`}
                          </span>
                          <span style={{ fontSize: "10px", fontFamily: "var(--mono)", background: "#eee9df", padding: "1px 6px", borderRadius: "4px", color: "#525048", flexShrink: 0 }}>
                            v{app.resume_version_no || "1"}
                          </span>
                        </div>
                        <div style={{ fontSize: "12px", color: "var(--text-soft)", marginTop: "2px" }}>
                          {app.job_company || "Direct Employer"}
                        </div>
                      </div>

                      {/* Ghosting badge */}
                      {app.is_ghosted && (
                        <div style={{ fontSize: "10px", color: "#bd7652", background: "rgba(189,118,82,0.12)", border: "1px solid rgba(189,118,82,0.25)", padding: "2px 6px", borderRadius: "4px", display: "flex", alignItems: "center", gap: "4px" }}>
                          <span>⚠️</span>
                          <span>{app.days_since_update || 14}d without an update · Follow up</span>
                        </div>
                      )}

                      {/* Tier 1: Primary Stage Advancement Button */}
                      {["pending", "review_required"].includes(app.status) && (
                        <button
                          type="button"
                          onClick={() => onReviewApplication(app.id)}
                          style={{ width: "100%", fontSize: "11px", padding: "6px 10px", borderRadius: "8px", background: "#bd7652", color: "#ffffff", border: "none", cursor: "pointer", fontWeight: 700, display: "flex", justifyContent: "center", alignItems: "center", gap: "4px", boxShadow: "0 1px 3px rgba(36,35,31,0.08)" }}
                        >
                          <span>Review Fields</span>
                          <span>➔</span>
                        </button>
                      )}
                      {app.status === "reviewed" && (
                        <button
                          type="button"
                          onClick={() => onMarkSubmitted(app.id)}
                          style={{ width: "100%", fontSize: "11px", padding: "6px 10px", borderRadius: "8px", background: "#15803d", color: "#ffffff", border: "none", cursor: "pointer", fontWeight: 700, display: "flex", justifyContent: "center", alignItems: "center", gap: "4px", boxShadow: "0 1px 3px rgba(36,35,31,0.08)" }}
                        >
                          <span>Confirm Applied</span>
                          <span>➔</span>
                        </button>
                      )}
                      {app.status === "applied" && (
                        <button
                          type="button"
                          onClick={() => onStatusChange(app.id, "screening")}
                          style={{ width: "100%", fontSize: "11px", padding: "6px 10px", borderRadius: "8px", background: "#5369d9", color: "#ffffff", border: "none", cursor: "pointer", fontWeight: 700, display: "flex", justifyContent: "center", alignItems: "center", gap: "4px", boxShadow: "0 1px 3px rgba(36,35,31,0.08)" }}
                        >
                          <span>Advance to Screen</span>
                          <span>➔</span>
                        </button>
                      )}
                      {app.status === "screening" && (
                        <button
                          type="button"
                          onClick={() => onStatusChange(app.id, "interviewing")}
                          style={{ width: "100%", fontSize: "11px", padding: "6px 10px", borderRadius: "8px", background: "#4052b3", color: "#ffffff", border: "none", cursor: "pointer", fontWeight: 700, display: "flex", justifyContent: "center", alignItems: "center", gap: "4px", boxShadow: "0 1px 3px rgba(36,35,31,0.08)" }}
                        >
                          <span>Advance to Tech Loop</span>
                          <span>➔</span>
                        </button>
                      )}
                      {app.status === "interviewing" && (
                        <button
                          type="button"
                          onClick={() => onStatusChange(app.id, "offer")}
                          style={{ width: "100%", fontSize: "11px", padding: "6px 10px", borderRadius: "8px", background: "#166534", color: "#ffffff", border: "none", cursor: "pointer", fontWeight: 700, display: "flex", justifyContent: "center", alignItems: "center", gap: "4px", boxShadow: "0 1px 3px rgba(36,35,31,0.08)" }}
                        >
                          <span>Mark Offer Received 🏆</span>
                        </button>
                      )}

                      {/* Tier 2: Secondary Quick Action Pill Bar */}
                      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "4px", paddingTop: "6px", borderTop: "1px solid rgba(36, 35, 31, 0.08)" }}>
                        <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                          {/* InMail outreach button */}
                          <button
                            type="button"
                            onClick={() => onOpenOutreach(app.id)}
                            style={{
                              fontSize: "11px",
                              padding: "3px 8px",
                              borderRadius: "6px",
                              background: "rgba(83, 105, 217, 0.1)",
                              color: "#5369d9",
                              border: "1px solid rgba(83, 105, 217, 0.25)",
                              cursor: "pointer",
                              fontWeight: 600,
                              display: "flex",
                              alignItems: "center",
                              gap: "3px",
                            }}
                            title="Generate AI recruiter InMail message"
                          >
                            <span>✉️</span>
                            <span>InMail</span>
                          </button>

                          {/* Quick portal link */}
                          {app.application_url && (
                            <a
                              href={app.application_url}
                              target="_blank"
                              rel="noreferrer"
                              style={{
                                fontSize: "11px",
                                padding: "3px 8px",
                                borderRadius: "6px",
                                background: "#faf7f0",
                                color: "#525048",
                                border: "1px solid rgba(36, 35, 31, 0.12)",
                                textDecoration: "none",
                                fontWeight: 500,
                                display: "flex",
                                alignItems: "center",
                                gap: "2px",
                              }}
                              title="Open original employer careers portal"
                            >
                              <span>🔗</span>
                              <span>Portal</span>
                            </a>
                          )}

                          {/* Ghosted button */}
                          {["applied", "screening"].includes(app.status) && (
                            <button
                              type="button"
                              onClick={() => onStatusChange(app.id, "ghosted")}
                              style={{
                                fontSize: "10px",
                                padding: "3px 6px",
                                borderRadius: "6px",
                                background: "rgba(189, 118, 82, 0.1)",
                                color: "#bd7652",
                                border: "1px solid rgba(189, 118, 82, 0.25)",
                                cursor: "pointer",
                                fontWeight: 500,
                              }}
                              title="Mark role ghosted after 14+ days silence"
                            >
                              👻 Ghost
                            </button>
                          )}
                        </div>

                        {/* Quick Stage Picker Dropdown */}
                        <select
                          value={app.status}
                          onChange={(e) => onStatusChange(app.id, e.target.value)}
                          style={{
                            fontSize: "10px",
                            fontFamily: "var(--mono)",
                            padding: "2px 4px",
                            borderRadius: "4px",
                            border: "1px solid rgba(36, 35, 31, 0.12)",
                            background: "#faf7f0",
                            color: "#706e68",
                            cursor: "pointer",
                            maxWidth: "76px",
                          }}
                          title="Jump directly to any pipeline stage"
                        >
                          <option value="bookmarked">Saved</option>
                          <option value="pending">Prep</option>
                          <option value="reviewed">Reviewed</option>
                          <option value="applied">Applied</option>
                          <option value="screening">Screen</option>
                          <option value="interviewing">Interview</option>
                          <option value="offer">Offer</option>
                          <option value="ghosted">Ghosted</option>
                        </select>
                      </div>
                    </div>
                  ))}
                  {!stageApps.length && (
                    <div style={{ textAlign: "center", color: "#99958d", fontSize: "12px", marginTop: "20px" }}>
                      No items
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* 4. Create Application Record Card */}
      <article className="mp-card rounded-2xl p-6 bg-[#faf7f0]/85 backdrop-blur-xl border border-[#24231f]/12 shadow-sm" style={{ marginBottom: "20px" }}>
        <h3>Create Application Record</h3>
        <p className="mp-muted">Target job: {targetLabel}</p>
        <div className="mp-grid three">
          <label>
            Resume version
            <select value={selectedVersionId} onChange={(event) => setSelectedVersionId(event.target.value)}>
              <option value="">Select a version</option>
              {versions.map((version) => (
                <option key={version.id} value={version.id}>v{version.version_no}</option>
              ))}
            </select>
          </label>
          <label>
            Status
            <select value={status} onChange={(event) => setStatus(event.target.value)}>
              <option value="draft">Draft</option>
              <option value="pending">Pending</option>
              <option value="review_required">Review Required</option>
              <option value="bookmarked">Bookmarked</option>
            </select>
          </label>
          <label>
            Application URL
            <input value={applicationUrl} onChange={(event) => setApplicationUrl(event.target.value)} placeholder="https://..." />
          </label>
        </div>
        <label>
          Notes
          <textarea rows={2} value={notes} onChange={(event) => setNotes(event.target.value)} placeholder="Follow-up date, contact, or next step" />
        </label>
        <button type="button" onClick={onCreate} disabled={busy || !jobDescriptionId || !selectedVersionId}>
          {busy ? "Saving..." : "Track Application"}
        </button>
        {info && <p className="mp-ok">{info}</p>}
        {error && <p className="mp-error">{error}</p>}
      </article>

      {/* 5. Detailed Table View (All Existing Functions & Diagnostics Preserved) */}
      {activeView === "table" && (
        <article className="mp-card rounded-2xl p-6 bg-[#faf7f0]/85 backdrop-blur-xl border border-[#24231f]/12 shadow-sm">
          <h3>Tracked Applications (Detailed List)</h3>
          <ul className="mp-list">
            {applications.map((application) => (
              <li key={application.id}>
                <strong>{application.job_title || `Job description #${application.job_description_id}`}</strong>
                <span>
                  {application.job_company || "Company not set"} | Resume v{application.resume_version_no || "?"} | Updated {formatDate(application.updated_at)}
                          {application.is_ghosted && <span style={{ color: "#bd7652", marginLeft: "8px" }}>(No update for {application.days_since_update}d)</span>}
                </span>
                <select
                  value={application.status}
                  aria-label={`Status for ${application.job_title || "application"}`}
                  onChange={(event) => onStatusChange(application.id, event.target.value)}
                >
                  <option value="draft">Draft</option>
                  <option value="pending">Pending</option>
                  <option value="review_required">Review Required</option>
                  <option value="reviewed" disabled>Reviewed</option>
                  <option value="applied" disabled>Applied</option>
                  <option value="screening">Screening</option>
                  <option value="interviewing">Interviewing</option>
                  <option value="offer">Offer</option>
                  <option value="ghosted">Ghosted</option>
                  <option value="rejected">Rejected</option>
                </select>
                {application.application_url && <a href={application.application_url} target="_blank" rel="noreferrer">Open application</a>}
                {application.autofill_payload && (
                  <pre className="mp-pre">{JSON.stringify(application.autofill_payload, null, 2)}</pre>
                )}
                {["pending", "review_required"].includes(application.status) && (
                  <button type="button" onClick={() => onReviewApplication(application.id)}>
                    Mark Reviewed
                  </button>
                )}
                {application.status === "reviewed" && (
                  <button type="button" onClick={() => onMarkSubmitted(application.id)}>
                    Mark Applied
                  </button>
                )}
                <button type="button" onClick={() => onOpenOutreach(application.id)}>
                  AI Outreach
                </button>
                {application.autofill_payload && (
                  <button type="button" onClick={() => onLoadBrowserPlan(application.id)}>
                    Browser Fill Plan
                  </button>
                )}
                <button type="button" onClick={() => onCheckAts(application.id)}>
                  Check ATS
                </button>
                <button type="button" onClick={() => onTriggerWorkflow(application.id, "application_reviewed")}>
                  n8n Event
                </button>
                {application.notes && <span>{application.notes}</span>}
              </li>
            ))}
            {!applications.length && <li>No applications tracked yet.</li>}
          </ul>
          {browserPlan && (
            <pre className="mp-pre">{JSON.stringify(browserPlan, null, 2)}</pre>
          )}
          {atsCompatibility && (
            <pre className="mp-pre">{JSON.stringify(atsCompatibility, null, 2)}</pre>
          )}
          {workflowResult && (
            <pre className="mp-pre">{JSON.stringify(workflowResult, null, 2)}</pre>
          )}
        </article>
      )}

      {/* 6. AI Recruiter Outreach & InMail Modal */}
      {outreachModal.open && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            backgroundColor: "rgba(36, 35, 31, 0.5)",
            backdropFilter: "blur(8px)",
            zIndex: 1000,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: "20px",
          }}
          onClick={() => setOutreachModal((prev) => ({ ...prev, open: false }))}
        >
          <div
            style={{
              background: "rgba(250, 247, 240, 0.95)",
              backdropFilter: "blur(24px)",
              WebkitBackdropFilter: "blur(24px)",
              border: "1px solid rgba(36, 35, 31, 0.15)",
              borderRadius: "20px",
              padding: "28px",
              maxWidth: "680px",
              width: "100%",
              maxHeight: "90vh",
              overflowY: "auto",
              boxShadow: "0 24px 60px rgba(36, 35, 31, 0.2)",
              color: "var(--ink)",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "16px" }}>
              <div>
                <span style={{ fontSize: "11px", letterSpacing: "1px", textTransform: "uppercase", color: "var(--brand)", fontWeight: 700 }}>
                  ClearHire AI Recruiter Drafter
                </span>
                <h3 style={{ margin: "4px 0 0" }}>
                  {outreachModal.data ? `${outreachModal.data.target_role} at ${outreachModal.data.target_company}` : "Generating Outreach..."}
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setOutreachModal((prev) => ({ ...prev, open: false }))}
                style={{ background: "transparent", border: "none", color: "var(--text-soft)", fontSize: "20px", cursor: "pointer" }}
              >
                ✕
              </button>
            </div>

            {outreachModal.loading && <p style={{ color: "var(--text-soft)" }}>Drafting high-converting personalized outreach...</p>}

            {outreachModal.data && (
              <>
                {/* Grounded highlights */}
                <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", marginBottom: "16px" }}>
                  {outreachModal.data.grounded_highlights?.map((h, i) => (
                    <span key={i} style={{ fontSize: "11px", background: "rgba(83, 105, 217, 0.08)", color: "var(--brand)", padding: "3px 8px", borderRadius: "6px" }}>
                      ✓ {h}
                    </span>
                  ))}
                </div>

                {/* Tabs */}
                <div style={{ display: "flex", gap: "8px", borderBottom: "1px solid var(--line)", paddingBottom: "8px", marginBottom: "14px" }}>
                  <button
                    type="button"
                    onClick={() => setOutreachModal((prev) => ({ ...prev, activeTab: "inmail" }))}
                    style={{
                      background: outreachModal.activeTab === "inmail" ? "var(--brand)" : "transparent",
                      color: outreachModal.activeTab === "inmail" ? "#ffffff" : "var(--ink)",
                      border: "none",
                      padding: "6px 12px",
                      borderRadius: "6px",
                      fontWeight: 600,
                      cursor: "pointer",
                      fontSize: "13px",
                    }}
                  >
                    Hiring Manager InMail
                  </button>
                  <button
                    type="button"
                    onClick={() => setOutreachModal((prev) => ({ ...prev, activeTab: "note" }))}
                    style={{
                      background: outreachModal.activeTab === "note" ? "var(--brand)" : "transparent",
                      color: outreachModal.activeTab === "note" ? "#ffffff" : "var(--ink)",
                      border: "none",
                      padding: "6px 12px",
                      borderRadius: "6px",
                      fontWeight: 600,
                      cursor: "pointer",
                      fontSize: "13px",
                    }}
                  >
                    LinkedIn Note (&lt;300 chars)
                  </button>
                  <button
                    type="button"
                    onClick={() => setOutreachModal((prev) => ({ ...prev, activeTab: "followup" }))}
                    style={{
                      background: outreachModal.activeTab === "followup" ? "var(--brand)" : "transparent",
                      color: outreachModal.activeTab === "followup" ? "#ffffff" : "var(--ink)",
                      border: "none",
                      padding: "6px 12px",
                      borderRadius: "6px",
                      fontWeight: 600,
                      cursor: "pointer",
                      fontSize: "13px",
                    }}
                  >
                    7-Day Follow-Up
                  </button>
                </div>

                {/* Active Tab Content */}
                <div style={{ position: "relative" }}>
                  <textarea
                    rows={8}
                    readOnly
                    value={
                      outreachModal.activeTab === "inmail"
                        ? outreachModal.data.hiring_manager_inmail
                        : outreachModal.activeTab === "note"
                        ? outreachModal.data.linkedin_connection_note
                        : outreachModal.data.follow_up_email
                    }
                    style={{
                      width: "100%",
                      background: "#ffffff",
                      border: "1px solid rgba(36, 35, 31, 0.15)",
                      borderRadius: "10px",
                      padding: "12px",
                      color: "var(--ink)",
                      fontFamily: "inherit",
                      fontSize: "14px",
                      lineHeight: "1.5",
                      resize: "none",
                    }}
                  />
                  {outreachModal.activeTab === "note" && (
                    <div style={{ fontSize: "11px", color: "var(--text-soft)", textAlign: "right", marginTop: "4px" }}>
                      Length: {outreachModal.data.linkedin_connection_note?.length || 0} / 300 characters (Strict limit)
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "16px", flexWrap: "wrap", gap: "10px" }}>
                  <a
                    href={outreachModal.data.linkedin_recruiter_search_url}
                    target="_blank"
                    rel="noreferrer"
                    style={{
                      background: "#ffffff",
                      border: "1px solid rgba(36, 35, 31, 0.15)",
                      padding: "8px 14px",
                      borderRadius: "8px",
                      color: "var(--ink)",
                      textDecoration: "none",
                      fontSize: "13px",
                      fontWeight: 600,
                      display: "flex",
                      alignItems: "center",
                      gap: "6px",
                    }}
                  >
                    🔍 Find {outreachModal.data.target_company} Recruiters on LinkedIn
                  </a>

                  <button
                    type="button"
                    onClick={() =>
                      onCopyOutreachText(
                        outreachModal.activeTab === "inmail"
                          ? outreachModal.data.hiring_manager_inmail
                          : outreachModal.activeTab === "note"
                          ? outreachModal.data.linkedin_connection_note
                          : outreachModal.data.follow_up_email
                      )
                    }
                    style={{
                      background: outreachModal.copied ? "#15803d" : "var(--brand)",
                      color: "#ffffff",
                      border: "none",
                      padding: "8px 18px",
                      borderRadius: "8px",
                      fontWeight: 700,
                      cursor: "pointer",
                      fontSize: "13px",
                    }}
                  >
                    {outreachModal.copied ? "✓ Copied to Clipboard!" : "📋 Copy Template"}
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </ModuleLayout>
  );
}
