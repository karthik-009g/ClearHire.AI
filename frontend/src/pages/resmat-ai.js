import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/router";
import ModuleLayout from "../components/ModuleLayout";
import { downloadTailoredPackage, getResumeDetail, listResumeVersions, reembedResume, tailorResume, uploadResume } from "../api/resumes";
import { formatPercent, getJdContext, getResmatContext, normalizeSkills, setResmatContext } from "../lib/moduleState";

export default function ResmatPage() {
  const router = useRouter();
  const [initialResumeContext] = useState(() => getResmatContext());
  const [file, setFile] = useState(null);
  const [resumeId, setResumeId] = useState(initialResumeContext?.resumeId || "");
  const [parsedSummary, setParsedSummary] = useState(initialResumeContext?.parsedSummary || null);
  const [versions, setVersions] = useState([]);
  const [jdContext] = useState(() => getJdContext());
  const [busy, setBusy] = useState(false);
  const [tailorBusy, setTailorBusy] = useState(false);
  const [packageBusy, setPackageBusy] = useState(false);
  const [tailorResult, setTailorResult] = useState(null);
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");

  const resumeSkills = useMemo(() => normalizeSkills(parsedSummary?.skills || []), [parsedSummary]);

  const loadVersions = useCallback(async (id) => {
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
  }, []);

  const syncResumeDetail = useCallback(async (id, options = {}) => {
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
  }, [loadVersions]);

  useEffect(() => {
    if (!resumeId) return undefined;
    // Load stored resume detail without triggering heavy re-embedding on every navigation.
    const frame = requestAnimationFrame(() => {
      syncResumeDetail(resumeId, { refreshEmbeddings: false, silent: true });
    });
    return () => cancelAnimationFrame(frame);
  }, [resumeId, syncResumeDetail]);

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

  const latestVersionNo = versions.length ? Math.max(...versions.map((version) => version.version_no || 1)) : 1;
  const latestSkillGap = jdContext?.skillGap || [];

  const onTailorForCurrentJd = async () => {
    if (!resumeId) {
      setError("Upload resume first before tailoring.");
      return;
    }

    if (!jdContext?.jdText || jdContext.jdText.trim().length < 20) {
      setError("Run JD Analyzer first so the Tailor Agent has a target job description.");
      return;
    }

    setError("");
    setInfo("");
    setTailorBusy(true);

    try {
      const payload = await tailorResume({
        resume_id: resumeId,
        source_version_no: latestVersionNo,
        jd_text: jdContext.jdText,
        role: jdContext.roleTitle || "Target Role",
        company: jdContext.companyName || null,
        source: "resmat-tailor-agent",
        include_cover_letter: false,
      });

      setTailorResult(payload);
      await loadVersions(resumeId);
      setInfo(`Tailor Agent created ATS-friendly resume v${payload.version_no}.`);
    } catch (err) {
      setError(err.message || "Tailor Agent failed.");
    } finally {
      setTailorBusy(false);
    }
  };

  const onDownloadApplyPackage = async () => {
    if (!resumeId || !jdContext?.jdText || jdContext.jdText.trim().length < 20) {
      setError("Upload a resume and run JD Analyzer before creating an apply-ready package.");
      return;
    }

    setError("");
    setInfo("");
    setPackageBusy(true);
    try {
      const result = await downloadTailoredPackage({
        resume_id: resumeId,
        source_version_no: latestVersionNo,
        jd_text: jdContext.jdText,
        role: jdContext.roleTitle || "Target Role",
        company: jdContext.companyName || null,
        source: "resmat-apply-package",
        include_cover_letter: true,
      });
      const url = URL.createObjectURL(result.blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = result.filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
      await loadVersions(resumeId);
      setInfo("Apply-ready package downloaded with a new tailored resume version.");
    } catch (err) {
      setError(err.message || "Could not create apply-ready package.");
    } finally {
      setPackageBusy(false);
    }
  };

  return (
    <ModuleLayout
      title="ResMat.ai Resume Analyzer"
      subtitle="Upload, parse, and maintain your resume intelligence context. This module feeds the JD Analyzer route."
    >
      <div className="mp-grid two">
        <article className="mp-card rounded-2xl p-6 bg-[#faf7f0]/85 backdrop-blur-xl border border-[#24231f]/12 shadow-sm">
          <h3>Resume Intake</h3>
          <p>Supported formats: PDF and DOCX (Strict 1-page budget enforced).</p>
          <div
            style={{
              border: "2px dashed rgba(36, 35, 31, 0.15)",
              borderRadius: "14px",
              padding: "16px",
              background: "rgba(255, 255, 255, 0.65)",
              backdropFilter: "blur(12px)",
              WebkitBackdropFilter: "blur(12px)",
              textAlign: "center",
              marginBottom: "14px",
            }}
          >
            <input
              type="file"
              accept=".pdf,.docx"
              onChange={(event) => setFile(event.target.files?.[0] || null)}
              style={{
                display: "block",
                width: "100%",
                fontSize: "12px",
                fontFamily: "var(--mono)",
                cursor: "pointer",
              }}
            />
            {file && (
              <span style={{ display: "block", marginTop: "8px", fontSize: "11px", color: "var(--brand)", fontFamily: "var(--mono)" }}>
                Selected: {file.name} ({(file.size / 1024).toFixed(1)} KB)
              </span>
            )}
          </div>
          <button type="button" onClick={onUpload} disabled={!file || busy}>
            {busy ? "Analyzing..." : "Run ResMat.ai Analysis"}
          </button>
          <div style={{ marginTop: "14px", display: "flex", flexDirection: "column", gap: "4px" }}>
            <p className="mp-muted" style={{ margin: 0 }}>Extraction and embeddings refresh automatically when this resume context loads.</p>
            <p className="mp-muted" style={{ margin: 0 }}>Resume ID: {resumeId || "Not uploaded"}</p>
          </div>
          {info && <p className="mp-ok" style={{ marginTop: "10px" }}>{info}</p>}
          {error && <p className="mp-error" style={{ marginTop: "10px" }}>{error}</p>}
        </article>

        <article className="mp-card rounded-2xl p-6 bg-[#faf7f0]/85 backdrop-blur-xl border border-[#24231f]/12 shadow-sm">
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
        <article className="mp-card rounded-2xl p-6 bg-[#faf7f0]/85 backdrop-blur-xl border border-[#24231f]/12 shadow-sm">
          <h3>Extracted Skills</h3>
          {resumeSkills.length === 0 && <p className="mp-muted">Upload a resume to extract skills.</p>}
          <div className="mp-chip-row">
            {resumeSkills.map((skill) => (
              <span key={skill} className="mp-chip">{skill}</span>
            ))}
          </div>
        </article>

        <article className="mp-card rounded-2xl p-6 bg-[#faf7f0]/85 backdrop-blur-xl border border-[#24231f]/12 shadow-sm">
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

      <article className="mp-card rounded-2xl p-6 bg-[#faf7f0]/85 backdrop-blur-xl border border-[#24231f]/12 shadow-sm">
        <h3>1-Page ATS Resume Synthesizer</h3>
        <p className="mp-muted">Compiles a strictly budgeted 1-page PDF tailored to the current JD keywords with zero page overflow.</p>
        <div style={{ display: "flex", gap: "10px", flexWrap: "wrap", margin: "14px 0" }}>
          <button
            type="button"
            onClick={onTailorForCurrentJd}
            disabled={!resumeId || tailorBusy}
            style={{
              padding: "10px 20px",
              borderRadius: "10px",
              background: "var(--brand)",
              color: "#ffffff",
              border: "none",
              fontWeight: 700,
              cursor: "pointer",
              boxShadow: "0 2px 8px rgba(83, 105, 217, 0.25)",
              display: "flex",
              alignItems: "center",
              gap: "6px",
            }}
          >
            <span>✨</span>
            <span>{tailorBusy ? "Synthesizing 1-Page PDF..." : "Synthesize 1-Page ATS Resume"}</span>
          </button>
          <button
            type="button"
            onClick={onDownloadApplyPackage}
            disabled={!resumeId || packageBusy}
            style={{
              padding: "10px 18px",
              borderRadius: "10px",
              background: "#24231f",
              color: "#ffffff",
              border: "none",
              fontWeight: 600,
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "6px",
            }}
          >
            <span>📦</span>
            <span>{packageBusy ? "Preparing Package..." : "Download Apply-Ready Package (.zip)"}</span>
          </button>
        </div>
        {tailorResult && (
          <>
            <div className="mp-grid three">
              <p>Total: {formatPercent(tailorResult.total_score)}</p>
              <p>Keyword: {formatPercent(tailorResult.keyword_score)}</p>
              <p>Embedding: {formatPercent(tailorResult.embedding_score)}</p>
            </div>
            <pre className="mp-pre">{tailorResult.tailored_resume_text}</pre>
          </>
        )}
      </article>

      <article className="mp-card rounded-2xl p-6 bg-[#faf7f0]/85 backdrop-blur-xl border border-[#24231f]/12 shadow-sm">
        <h3>Parsed Summary (Raw)</h3>
        <pre className="mp-pre">{parsedSummary ? JSON.stringify(parsedSummary, null, 2) : "No parsed summary yet."}</pre>
      </article>
    </ModuleLayout>
  );
}
