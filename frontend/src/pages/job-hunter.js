import { useEffect, useMemo, useState } from "react";
import ModuleLayout from "../components/ModuleLayout";
import { scrapeJobs } from "../api/jobs";
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
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");
  const [results, setResults] = useState([]);

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
        <h3>Matched Jobs</h3>
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
    </ModuleLayout>
  );
}
