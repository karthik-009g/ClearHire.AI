import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/router";
import ModuleLayout from "../components/ModuleLayout";
import { scrapeJobs } from "../api/jobs";
import { matchResume } from "../api/resumes";
import {
  computeSkillGap,
  extractSkillKeywords,
  formatPercent,
  getJdContext,
  getResmatContext,
  inferTargetSkills,
  normalizeSkills,
  setJdContext,
} from "../lib/moduleState";

const DEFAULT_SOURCES = ["linkedin", "naukri"];

function buildSearchKeywords(jdText, roleTitle, companyName) {
  const baseline = extractSkillKeywords(jdText);
  const fromText = `${roleTitle} ${companyName} ${jdText}`
    .toLowerCase()
    .split(/[^a-z0-9+#.]+/)
    .filter((token) => token.length >= 3)
    .slice(0, 8);

  const set = new Set(baseline.map((token) => token.toLowerCase()));
  for (const token of fromText) {
    set.add(token);
  }

  return Array.from(set).slice(0, 12);
}

export default function JdAnalyzerPage() {
  const router = useRouter();
  const [resmatContext, setResmatContextState] = useState(null);
  const [roleTitle, setRoleTitle] = useState("AI Engineer");
  const [companyName, setCompanyName] = useState("");
  const [jdText, setJdText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");
  const [analysis, setAnalysis] = useState(null);

  useEffect(() => {
    const resumeContext = getResmatContext();
    setResmatContextState(resumeContext);

    const existing = getJdContext();
    if (existing) {
      setAnalysis(existing);
      setRoleTitle(existing.roleTitle || "AI Engineer");
      setCompanyName(existing.companyName || "");
      setJdText(existing.jdText || "");
    }
  }, []);

  const resumeSkills = useMemo(() => normalizeSkills(resmatContext?.parsedSummary?.skills || []), [resmatContext]);

  const onAnalyze = async () => {
    if (!resmatContext?.resumeId) {
      setError("Upload resume first in ResMat.ai module.");
      return;
    }

    if (jdText.trim().length < 20) {
      setError("Paste at least 20 characters of JD text.");
      return;
    }

    setBusy(true);
    setError("");
    setInfo("");

    try {
      const match = await matchResume({
        resume_id: resmatContext.resumeId,
        jd_text: jdText,
        title: roleTitle,
        company: companyName || null,
        source: "jd-analyzer-route",
      });

      let scrapePayload = { jobs: [], top_matches: [], scraped_count: 0 };
      try {
        scrapePayload = await scrapeJobs({
          sources: DEFAULT_SOURCES,
          keywords: buildSearchKeywords(jdText, roleTitle, companyName),
          resume_id: resmatContext.resumeId,
          send_email: false,
          posted_within_hours: 72,
        });
      } catch (scrapeErr) {
        setInfo(`JD score generated. Market scan partially unavailable: ${scrapeErr.message}`);
      }

      const marketSignals = scrapePayload.top_matches?.length
        ? scrapePayload.top_matches
        : scrapePayload.jobs || [];

      const generatedStack = inferTargetSkills(`${jdText} ${roleTitle} ${companyName}`, marketSignals);
      const skillGap = computeSkillGap(resumeSkills, generatedStack);

      const payload = {
        roleTitle,
        companyName,
        jdText,
        match,
        generatedStack,
        skillGap,
        marketSignals: marketSignals.slice(0, 12),
        scrapedCount: scrapePayload.scraped_count || 0,
        analyzedAt: new Date().toISOString(),
      };

      setAnalysis(payload);
      setJdContext(payload);
      setInfo("JD Analyzer completed. Skills and match data are available for all downstream modules.");
    } catch (err) {
      setError(err.message || "JD Analyzer failed.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <ModuleLayout
      title="JD Analyzer"
      subtitle="Input JD and company, score against resume, generate target tech stack, and produce skill gap analytics."
    >
      <article className="mp-card">
        <div className="mp-grid three">
          <label>
            Target role
            <input value={roleTitle} onChange={(event) => setRoleTitle(event.target.value)} placeholder="AI Engineer" />
          </label>
          <label>
            Company name
            <input value={companyName} onChange={(event) => setCompanyName(event.target.value)} placeholder="Company" />
          </label>
          <label>
            Resume source
            <input value={resmatContext?.resumeId || "Missing"} disabled />
          </label>
        </div>

        <label>
          Job description
          <textarea
            rows={9}
            value={jdText}
            onChange={(event) => setJdText(event.target.value)}
            placeholder="Paste complete JD text here"
          />
        </label>

        <button type="button" onClick={onAnalyze} disabled={busy}>
          {busy ? "Analyzing..." : "Run JD Analyzer"}
        </button>
        {info && <p className="mp-ok">{info}</p>}
        {error && <p className="mp-error">{error}</p>}
      </article>

      <div className="mp-grid three">
        <article className="mp-card">
          <h3>Match Score</h3>
          <p className="mp-metric">{formatPercent(analysis?.match?.total_score)}</p>
          <p>Keyword: {formatPercent(analysis?.match?.keyword_score)}</p>
          <p>Embedding: {formatPercent(analysis?.match?.embedding_score)}</p>
        </article>
        <article className="mp-card">
          <h3>Market Signals</h3>
          <p className="mp-metric">{analysis?.scrapedCount ?? 0}</p>
          <p>LinkedIn + Naukri scan results integrated.</p>
        </article>
        <article className="mp-card">
          <h3>Skill Gap Count</h3>
          <p className="mp-metric">{analysis?.skillGap?.length ?? 0}</p>
          <p>Auto-compared against your resume skills.</p>
        </article>
      </div>

      <div className="mp-grid two">
        <article className="mp-card">
          <h3>AI Generated Target Stack</h3>
          <div className="mp-chip-row">
            {(analysis?.generatedStack || []).map((skill) => (
              <span key={skill} className="mp-chip">{skill}</span>
            ))}
            {!(analysis?.generatedStack || []).length && <p className="mp-muted">Run analyzer to generate stack.</p>}
          </div>
        </article>

        <article className="mp-card">
          <h3>Skill Gap Map</h3>
          <div className="mp-chip-row">
            {(analysis?.skillGap || []).map((skill) => (
              <span key={skill} className="mp-chip warning">{skill}</span>
            ))}
            {!(analysis?.skillGap || []).length && <p className="mp-muted">No missing skills identified yet.</p>}
          </div>
        </article>
      </div>

      <article className="mp-card">
        <h3>Top Market Matches</h3>
        <ul className="mp-list">
          {(analysis?.marketSignals || []).map((job) => (
            <li key={`${job.id}-${job.url}`}>
              <strong>{job.title}</strong>
              <span>{job.company} | {job.source} | Score {formatPercent(job.score)}</span>
              <a href={job.url} target="_blank" rel="noreferrer">Open Job</a>
            </li>
          ))}
          {!(analysis?.marketSignals || []).length && <li>No market matches yet.</li>}
        </ul>
        <button type="button" onClick={() => router.push("/job-hunter")}>Send To Job Hunter</button>
      </article>
    </ModuleLayout>
  );
}
