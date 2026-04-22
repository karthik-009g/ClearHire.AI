import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/router";
import ModuleLayout from "../components/ModuleLayout";
import { getResumeDetail, listResumeVersions, reembedResume, uploadResume } from "../api/resumes";
import { formatPercent, getJdContext, getResmatContext, normalizeSkills, setResmatContext } from "../lib/moduleState";

export default function ResmatPage() {
  const router = useRouter();
  const [file, setFile] = useState(null);
  const [resumeId, setResumeId] = useState("");
  const [parsedSummary, setParsedSummary] = useState(null);
  const [versions, setVersions] = useState([]);
  const [jdContext, setJdContextState] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");

  const resumeSkills = useMemo(() => normalizeSkills(parsedSummary?.skills || []), [parsedSummary]);

  useEffect(() => {
    const existing = getResmatContext();
    if (existing?.resumeId) {
      setResumeId(existing.resumeId);
      // Keep stored resumes in sync with the latest parser/embedding pipeline automatically.
      syncResumeDetail(existing.resumeId, { refreshEmbeddings: true, silent: true });
    }

    setJdContextState(getJdContext());
  }, []);

  const syncResumeDetail = async (id, options = {}) => {
    const { refreshEmbeddings = false, silent = false } = options;
    if (!id) {
      return;
    }

    try {
      if (refreshEmbeddings) {
        await reembedResume(id);
      }

      const detail = await getResumeDetail(id);
      setParsedSummary(detail.parsed_summary || null);
      setResmatContext({
        resumeId: detail.id,
        parsedSummary: detail.parsed_summary || null,
        originalFilename: detail.original_filename,
        createdAt: detail.created_at,
      });
      await loadVersions(id);
      if (refreshEmbeddings && !silent) {
        setInfo("Resume extraction and embeddings refreshed from latest parser.");
      }
    } catch {
      if (refreshEmbeddings && !silent) {
        setError("Could not refresh parsed summary right now.");
      }
    }
  };

  const loadVersions = async (id) => {
    if (!id) {
      setVersions([]);
      return;
    }

    try {
      const payload = await listResumeVersions(id);
      setVersions(payload.versions || []);
    } catch {
      setVersions([]);
    }
  };

  const onUpload = async () => {
    if (!file) {
      return;
    }

    setError("");
    setInfo("");
    setBusy(true);

    try {
      const payload = await uploadResume(file);
      const nextContext = {
        resumeId: payload.resume_id,
        parsedSummary: payload.parsed_summary,
        originalFilename: payload.original_filename,
        createdAt: payload.created_at,
      };

      setResumeId(payload.resume_id);
      setParsedSummary(payload.parsed_summary || null);
      setResmatContext(nextContext);
      await loadVersions(payload.resume_id);
      setInfo("ResMat.ai analysis completed. Resume context is ready for JD Analyzer.");
    } catch (err) {
      setError(err.message || "Resume upload failed.");
    } finally {
      setBusy(false);
    }
  };

  const latestSkillGap = jdContext?.skillGap || [];

  return (
    <ModuleLayout
      title="ResMat.ai Resume Analyzer"
      subtitle="Upload, parse, and maintain your resume intelligence context. This module feeds the JD Analyzer route."
    >
      <div className="mp-grid two">
        <article className="mp-card">
          <h3>Resume Intake</h3>
          <p>Supported formats: PDF and DOCX.</p>
          <input type="file" accept=".pdf,.docx" onChange={(event) => setFile(event.target.files?.[0] || null)} />
          <button type="button" onClick={onUpload} disabled={!file || busy}>
            {busy ? "Analyzing..." : "Run ResMat.ai Analysis"}
          </button>
          <p className="mp-muted">Extraction and embeddings refresh automatically when this resume context loads.</p>
          <p className="mp-muted">Resume ID: {resumeId || "Not uploaded"}</p>
          {info && <p className="mp-ok">{info}</p>}
          {error && <p className="mp-error">{error}</p>}
        </article>

        <article className="mp-card">
          <h3>Version Timeline</h3>
          {versions.length === 0 && <p className="mp-muted">No versions available yet.</p>}
          <ul className="mp-list">
            {versions.map((version) => (
              <li key={version.id}>
                <strong>v{version.version_no}</strong>
                <span>{new Date(version.created_at).toLocaleString()}</span>
              </li>
            ))}
          </ul>
        </article>
      </div>

      <div className="mp-grid two">
        <article className="mp-card">
          <h3>Extracted Skills</h3>
          {resumeSkills.length === 0 && <p className="mp-muted">Upload a resume to extract skills.</p>}
          <div className="mp-chip-row">
            {resumeSkills.map((skill) => (
              <span key={skill} className="mp-chip">{skill}</span>
            ))}
          </div>
        </article>

        <article className="mp-card">
          <h3>Skill Gap Map (Sub-module)</h3>
          <p>Latest match score: {formatPercent(jdContext?.match?.total_score)}</p>
          {latestSkillGap.length === 0 ? (
            <p className="mp-muted">Run JD Analyzer to compute skill gaps.</p>
          ) : (
            <div className="mp-chip-row">
              {latestSkillGap.map((skill) => (
                <span key={skill} className="mp-chip warning">{skill}</span>
              ))}
            </div>
          )}
          <button type="button" onClick={() => router.push("/jd-analyzer")}>Send Context To JD Analyzer</button>
        </article>
      </div>

      <article className="mp-card">
        <h3>Parsed Summary (Raw)</h3>
        <pre className="mp-pre">{parsedSummary ? JSON.stringify(parsedSummary, null, 2) : "No parsed summary yet."}</pre>
      </article>
    </ModuleLayout>
  );
}
