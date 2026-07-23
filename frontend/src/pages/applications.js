import { useCallback, useEffect, useMemo, useState } from "react";
import ModuleLayout from "../components/ModuleLayout";
import { createApplication, listApplications, updateApplicationStatus } from "../api/applications";
import { listResumeVersions } from "../api/resumes";
import { getJdContext, getResmatContext } from "../lib/moduleState";

function formatDate(value) {
  if (!value) {
    return "Not available";
  }

  return new Date(value).toLocaleString();
}

export default function ApplicationsPage() {
  const [resumeContext, setResumeContext] = useState(null);
  const [jdContext, setJdContext] = useState(null);
  const [versions, setVersions] = useState([]);
  const [selectedVersionId, setSelectedVersionId] = useState("");
  const [status, setStatus] = useState("pending");
  const [applicationUrl, setApplicationUrl] = useState("");
  const [notes, setNotes] = useState("");
  const [applications, setApplications] = useState([]);
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

  const loadApplications = useCallback(async () => {
    const payload = await listApplications();
    setApplications(payload || []);
  }, []);

  useEffect(() => {
    const resume = getResmatContext();
    setResumeContext(resume);
    setJdContext(getJdContext());

    const load = async () => {
      try {
        await loadApplications();
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
  }, [loadApplications]);

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
      await loadApplications();
      setInfo("Application record created.");
    } catch (err) {
      setError(err.message || "Could not create application record.");
    } finally {
      setBusy(false);
    }
  };

  const onStatusChange = async (applicationId, nextStatus) => {
    setError("");
    try {
      const current = applications.find((application) => application.id === applicationId);
      await updateApplicationStatus(applicationId, nextStatus, current?.notes || "");
      await loadApplications();
    } catch (err) {
      setError(err.message || "Could not update application status.");
    }
  };

  return (
    <ModuleLayout
      title="Applications"
      subtitle="Track each target role from pending to applied with the exact resume version used."
    >
      <article className="mp-card">
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
              <option value="pending">Pending</option>
              <option value="applied">Applied</option>
            </select>
          </label>
          <label>
            Application URL
            <input value={applicationUrl} onChange={(event) => setApplicationUrl(event.target.value)} placeholder="https://..." />
          </label>
        </div>
        <label>
          Notes
          <textarea rows={3} value={notes} onChange={(event) => setNotes(event.target.value)} placeholder="Follow-up date, contact, or next step" />
        </label>
        <button type="button" onClick={onCreate} disabled={busy || !jobDescriptionId || !selectedVersionId}>
          {busy ? "Saving..." : "Track Application"}
        </button>
        {info && <p className="mp-ok">{info}</p>}
        {error && <p className="mp-error">{error}</p>}
      </article>

      <article className="mp-card">
        <h3>Tracked Applications</h3>
        <ul className="mp-list">
          {applications.map((application) => (
            <li key={application.id}>
              <strong>{application.job_title || `Job description #${application.job_description_id}`}</strong>
              <span>
                {application.job_company || "Company not set"} | Resume v{application.resume_version_no || "?"} | Updated {formatDate(application.updated_at)}
              </span>
              <select
                value={application.status}
                aria-label={`Status for ${application.job_title || "application"}`}
                onChange={(event) => onStatusChange(application.id, event.target.value)}
              >
                <option value="pending">Pending</option>
                <option value="applied">Applied</option>
              </select>
              {application.application_url && <a href={application.application_url} target="_blank" rel="noreferrer">Open application</a>}
              {application.notes && <span>{application.notes}</span>}
            </li>
          ))}
          {!applications.length && <li>No applications tracked yet.</li>}
        </ul>
      </article>
    </ModuleLayout>
  );
}
