import { useEffect, useMemo, useState } from "react";
import ModuleLayout from "../components/ModuleLayout";
import { scrapeJobs } from "../api/jobs";
import { listResumeVersions, tailorResume } from "../api/resumes";
import {
  formatPercent,
  getJdContext,
  getResmatContext,
  normalizeSkills,
  parseCsv,
} from "../lib/moduleState";

export default function JobHunterPage() {
  const [resumeContext, setResumeContext] = useState(null);
  const [jdContext, setJdContextState] = useState(null);
  const [sourcesText, setSourcesText] = useState("linkedin, naukri");
  const [keywordsText, setKeywordsText] = useState("");
  const [postedWithinHours, setPostedWithinHours] = useState(72);
  const [busy, setBusy] = useState(false);
  const [tailorBusy, setTailorBusy] = useState(false);
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");
  const [results, setResults] = useState([]);
  const [tailorResult, setTailorResult] = useState(null);

  useEffect(() => {
    const resume = getResmatContext();
    const jd = getJdContext();
    setResumeContext(resume);
    setJdContextState(jd);

    if (jd?.generatedStack?.length) {
      setKeywordsText(jd.generatedStack.slice(0, 8).join(", "));
    } else {
      setKeywordsText("python, fastapi, llm, machine learning");
    }
  }, []);

  const resumeSkills = useMemo(() => normalizeSkills(resumeContext?.parsedSummary?.skills || []), [resumeContext]);

  const onSearch = async () => {
    setBusy(true);
    setError("");
    setInfo("");

    try {
      const payload = await scrapeJobs({
        sources: parseCsv(sourcesText),
        keywords: parseCsv(keywordsText),
        resume_id: resumeContext?.resumeId || null,
        send_email: false,
        posted_within_hours: Number(postedWithinHours) || 72,
      });

      const ranked = payload.top_matches?.length ? payload.top_matches : payload.jobs || [];
      setResults(ranked);
      setInfo(`Job Hunter found ${ranked.length} ranked opportunities.`);
    } catch (err) {
      setError(err.message || "Job search failed.");
    } finally {
      setBusy(false);
    }
  };

  const buildJobsBrief = () => {
    const selected = results.slice(0, 10);
    const lines = selected.flatMap((job, index) => [
      `Job ${index + 1}: ${job.title || "Untitled"} at ${job.company || "Unknown"}`,
      `Source: ${job.source || "job-hunter"} | Location: ${job.location || "India"}`,
      `Description: ${job.description || job.title || ""}`,
    ]);

    return [
      "Tailor the resume toward the common requirements across these currently ranked jobs.",
      "Keep the resume ATS-friendly, one page, and do not invent experience.",
      ...lines,
    ].join("\n");
  };

  const latestVersionNo = async () => {
    if (!resumeContext?.resumeId) {
      return 1;
    }

    try {
      const payload = await listResumeVersions(resumeContext.resumeId);
      const versions = payload.versions || [];
      return versions.length ? Math.max(...versions.map((version) => version.version_no || 1)) : 1;
    } catch {
      return 1;
    }
  };

  const onTailorForCurrentJobs = async () => {
    if (!resumeContext?.resumeId) {
      setError("Upload resume first in ResMat.ai before tailoring for jobs.");
      return;
    }

    if (!results.length) {
      setError("Search and rank jobs first so the Tailor Agent has current jobs.");
      return;
    }

    setError("");
    setInfo("");
    setTailorBusy(true);

    try {
      const versionNo = await latestVersionNo();
      const payload = await tailorResume({
        resume_id: resumeContext.resumeId,
        source_version_no: versionNo,
        jd_text: buildJobsBrief(),
        role: keywordsText || "Matched Job Set",
        company: "Current Job Hunter results",
        source: "job-hunter-tailor-agent",
        include_cover_letter: false,
      });

      setTailorResult(payload);
      setInfo(`Tailor Agent created one-page ATS resume v${payload.version_no} for current ranked jobs.`);
    } catch (err) {
      setError(err.message || "Tailor Agent failed.");
    } finally {
      setTailorBusy(false);
    }
  };

  return (
    <ModuleLayout
      title="Job Hunter"
      subtitle="Search jobs automatically, rank them against resume context, and return a prioritized list."
    >
      <article className="mp-card">
        <div className="mp-grid three">
          <label>
            Sources
            <input value={sourcesText} onChange={(event) => setSourcesText(event.target.value)} />
          </label>
          <label>
            Keywords
            <input value={keywordsText} onChange={(event) => setKeywordsText(event.target.value)} />
          </label>
          <label>
            Posted within hours
            <input
              type="number"
              min={1}
              max={336}
              value={postedWithinHours}
              onChange={(event) => setPostedWithinHours(Number(event.target.value) || 72)}
            />
          </label>
        </div>

        <p className="mp-muted">Resume context: {resumeContext?.resumeId || "Missing"}</p>
        <button type="button" onClick={onSearch} disabled={busy}>
          {busy ? "Searching..." : "Search and Rank Jobs"}
        </button>
        {info && <p className="mp-ok">{info}</p>}
        {error && <p className="mp-error">{error}</p>}
      </article>

      <div className="mp-grid two">
        <article className="mp-card">
          <h3>Resume Skill Context</h3>
          <div className="mp-chip-row">
            {resumeSkills.map((skill) => (
              <span key={skill} className="mp-chip">{skill}</span>
            ))}
            {!resumeSkills.length && <p className="mp-muted">No resume skills found yet.</p>}
          </div>
        </article>

        <article className="mp-card">
          <h3>Current Target Stack</h3>
          <div className="mp-chip-row">
            {(jdContext?.generatedStack || []).map((skill) => (
              <span key={skill} className="mp-chip">{skill}</span>
            ))}
            {!(jdContext?.generatedStack || []).length && <p className="mp-muted">No JD stack in memory yet.</p>}
          </div>
        </article>
      </div>

      <article className="mp-card">
        <div className="mp-card-head">
          <button type="button" className="mp-side-action" onClick={onTailorForCurrentJobs} disabled={tailorBusy || !results.length}>
            {tailorBusy ? "Tailoring..." : "Tailor Resume"}
          </button>
          <h3>Matched Jobs</h3>
        </div>
        <ul className="mp-list">
          {results.map((job) => (
            <li key={`${job.id}-${job.url}`}>
              <strong>{job.title}</strong>
              <span>{job.company} | {job.source} | Score {formatPercent(job.score)}</span>
              <a href={job.url} target="_blank" rel="noreferrer">Open Job</a>
            </li>
          ))}
          {!results.length && <li>No jobs listed yet. Run a search.</li>}
        </ul>
      </article>

      {tailorResult && (
        <article className="mp-card">
          <h3>Tailored Resume For Current Jobs</h3>
          <div className="mp-grid three">
            <p>Total: {formatPercent(tailorResult.total_score)}</p>
            <p>Keyword: {formatPercent(tailorResult.keyword_score)}</p>
            <p>Embedding: {formatPercent(tailorResult.embedding_score)}</p>
          </div>
          <pre className="mp-pre">{tailorResult.tailored_resume_text}</pre>
        </article>
      )}
    </ModuleLayout>
  );
}
