import { useMemo, useState } from "react";
import { uploadResume, matchResume, tailorResume } from "../api/resumes";
import { API_BASE } from "../api/client";

export default function HomePage() {
  const [file, setFile] = useState(null);
  const [resumeId, setResumeId] = useState("");
  const [jdText, setJdText] = useState("");
  const [role, setRole] = useState("Backend Engineer");
  const [company, setCompany] = useState("Acme");
  const [includeCoverLetter, setIncludeCoverLetter] = useState(true);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const canRunMatch = useMemo(() => resumeId && jdText.trim().length >= 20, [resumeId, jdText]);

  const onUpload = async () => {
    if (!file) return;
    setError("");
    setLoading(true);
    try {
      const data = await uploadResume(file);
      setResumeId(data.resume_id);
      setResult({ upload: data });
    } catch (err) {
      setError(err.message || "Upload failed");
    } finally {
      setLoading(false);
    }
  };

  const onMatch = async () => {
    if (!canRunMatch) return;
    setError("");
    setLoading(true);
    try {
      const data = await matchResume({ resume_id: resumeId, jd_text: jdText, title: role, company, source: "frontend" });
      setResult((prev) => ({ ...(prev || {}), match: data }));
    } catch (err) {
      setError(err.message || "Match failed");
    } finally {
      setLoading(false);
    }
  };

  const onTailor = async () => {
    if (!canRunMatch) return;
    setError("");
    setLoading(true);
    try {
      const data = await tailorResume({
        resume_id: resumeId,
        jd_text: jdText,
        role,
        company,
        source: "frontend",
        candidate_name: "Candidate",
        include_cover_letter: includeCoverLetter,
      });
      setResult((prev) => ({ ...(prev || {}), tailor: data }));
    } catch (err) {
      setError(err.message || "Tailor failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="page">
      <section className="hero">
        <p className="eyebrow">Agentic Job Application Assistant</p>
        <h1>Resume Match and Tailor</h1>
        <p className="sub">Backend API: {API_BASE}</p>
      </section>

      <section className="card">
        <h2>1) Upload Resume</h2>
        <input type="file" accept=".pdf,.docx" onChange={(e) => setFile(e.target.files?.[0] || null)} />
        <button onClick={onUpload} disabled={!file || loading}>{loading ? "Working..." : "Upload Resume"}</button>
        {resumeId && <p className="ok">Resume ID: {resumeId}</p>}
      </section>

      <section className="card">
        <h2>2) Job Description</h2>
        <div className="grid">
          <input value={role} onChange={(e) => setRole(e.target.value)} placeholder="Role" />
          <input value={company} onChange={(e) => setCompany(e.target.value)} placeholder="Company" />
        </div>
        <textarea value={jdText} onChange={(e) => setJdText(e.target.value)} rows={8} placeholder="Paste job description (min 20 chars)" />
        <label className="check">
          <input type="checkbox" checked={includeCoverLetter} onChange={(e) => setIncludeCoverLetter(e.target.checked)} />
          Include cover letter in apply-ready package
        </label>
        <div className="actions">
          <button onClick={onMatch} disabled={!canRunMatch || loading}>Run Match</button>
          <button onClick={onTailor} disabled={!canRunMatch || loading}>Tailor Resume</button>
        </div>
      </section>

      {error && <p className="error">{error}</p>}

      <section className="card">
        <h2>3) Results</h2>
        <pre>{JSON.stringify(result, null, 2)}</pre>
      </section>
    </main>
  );
}
