import { useMemo, useState } from "react";
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
  const [initialContexts] = useState(() => ({ resume: getResmatContext(), job: getJdContext() }));
  const [resmatContext] = useState(initialContexts.resume);
  const [roleTitle, setRoleTitle] = useState(initialContexts.job?.roleTitle || "AI Engineer");
  const [companyName, setCompanyName] = useState(initialContexts.job?.companyName || "");
  const [jdText, setJdText] = useState(initialContexts.job?.jdText || "");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");
  const [analysis, setAnalysis] = useState(initialContexts.job);

  const handleLoadSampleJd = () => {
    setRoleTitle("Senior Backend / AI Systems Engineer");
    setCompanyName("Razorpay");
    setJdText(
      "We are looking for a Senior Backend & AI Systems Engineer to build high-concurrency payment and merchant intelligence pipelines.\n\n" +
      "Key Requirements:\n" +
      "- 4+ years designing production microservices in Python, FastAPI, and Go.\n" +
      "- Experience designing low-latency REST and gRPC APIs handling 100K+ RPM.\n" +
      "- Hands-on expertise with PostgreSQL, Redis cache invalidation, and Apache Kafka.\n" +
      "- Familiarity with LLM orchestration, LangChain/LlamaIndex, vector databases (Pinecone/Milvus), and RAG pipelines.\n" +
      "- Docker, Kubernetes, AWS/GCP, and CI/CD automation."
    );
    setInfo("Sample Razorpay AI Systems JD loaded. Ready to analyze.");
  };

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
      <article className="mp-card rounded-2xl p-6 bg-[#faf7f0]/85 backdrop-blur-xl border border-[#24231f]/12 shadow-sm hover:border-[#24231f]/20 transition-all">
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

        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px", marginTop: "12px" }}>
          <label style={{ margin: 0, fontWeight: 600 }}>Job description</label>
          <button
            type="button"
            onClick={handleLoadSampleJd}
            style={{ fontSize: "11px", padding: "3px 10px", borderRadius: "999px", background: "rgba(83, 105, 217, 0.1)", color: "#5369d9", border: "1px solid rgba(83, 105, 217, 0.25)", cursor: "pointer", fontWeight: 600 }}
          >
            ⚡ Load Sample AI Systems JD
          </button>
        </div>

        <textarea
          rows={9}
          value={jdText}
          onChange={(event) => setJdText(event.target.value)}
          placeholder="Paste complete JD text here"
        />

        <div style={{ display: "flex", gap: "10px", alignItems: "center", marginTop: "12px", flexWrap: "wrap" }}>
          <button
            type="button"
            onClick={onAnalyze}
            disabled={busy}
            style={{
              padding: "10px 22px",
              borderRadius: "10px",
              background: "var(--brand)",
              color: "#ffffff",
              border: "none",
              fontWeight: 700,
              cursor: "pointer",
              boxShadow: "0 2px 8px rgba(83, 105, 217, 0.25)",
            }}
          >
            {busy ? "Analyzing Match & Market..." : "🚀 Run JD Analyzer"}
          </button>

          {analysis && (
            <>
              <button
                type="button"
                onClick={() => router.push("/resmat-ai")}
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
                <span>📄</span>
                <span>Tailor 1-Page Resume ➔</span>
              </button>
              <button
                type="button"
                onClick={() => router.push("/job-hunter")}
                style={{
                  padding: "10px 18px",
                  borderRadius: "10px",
                  background: "rgba(255, 255, 255, 0.8)",
                  color: "#24231f",
                  border: "1px solid rgba(36, 35, 31, 0.15)",
                  fontWeight: 600,
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                }}
              >
                <span>🎯</span>
                <span>Scan Matching Requisitions ➔</span>
              </button>
            </>
          )}
        </div>
        {info && <p className="mp-ok">{info}</p>}
        {error && <p className="mp-error">{error}</p>}
      </article>

      <div className="mp-grid three">
        <article className="mp-card rounded-2xl p-6 bg-[#faf7f0]/85 backdrop-blur-xl border border-[#24231f]/12 shadow-sm hover:border-[#24231f]/20 transition-all">
          <h3>Match Score</h3>
          <p className="mp-metric">{formatPercent(analysis?.match?.total_score)}</p>
          <p>Keyword: {formatPercent(analysis?.match?.keyword_score)}</p>
          <p>Embedding: {formatPercent(analysis?.match?.embedding_score)}</p>
        </article>
        <article className="mp-card rounded-2xl p-6 bg-[#faf7f0]/85 backdrop-blur-xl border border-[#24231f]/12 shadow-sm hover:border-[#24231f]/20 transition-all">
          <h3>Market Signals</h3>
          <p className="mp-metric">{analysis?.scrapedCount ?? 0}</p>
          <p>LinkedIn + Naukri scan results integrated.</p>
        </article>
        <article className="mp-card rounded-2xl p-6 bg-[#faf7f0]/85 backdrop-blur-xl border border-[#24231f]/12 shadow-sm hover:border-[#24231f]/20 transition-all">
          <h3>Skill Gap Count</h3>
          <p className="mp-metric">{analysis?.skillGap?.length ?? 0}</p>
          <p>Auto-compared against your resume skills.</p>
        </article>
      </div>

      <div className="mp-grid two">
        <article className="mp-card rounded-2xl p-6 bg-[#faf7f0]/85 backdrop-blur-xl border border-[#24231f]/12 shadow-sm hover:border-[#24231f]/20 transition-all">
          <h3>AI Generated Target Stack</h3>
          <div className="mp-chip-row">
            {(analysis?.generatedStack || []).map((skill) => (
              <span key={skill} className="mp-chip">{skill}</span>
            ))}
            {!(analysis?.generatedStack || []).length && <p className="mp-muted">Run analyzer to generate stack.</p>}
          </div>
        </article>

        <article className="mp-card rounded-2xl p-6 bg-[#faf7f0]/85 backdrop-blur-xl border border-[#24231f]/12 shadow-sm hover:border-[#24231f]/20 transition-all">
          <h3>Skill Gap Map</h3>
          <div className="mp-chip-row">
            {(analysis?.skillGap || []).map((skill) => (
              <span key={skill} className="mp-chip warning">{skill}</span>
            ))}
            {!(analysis?.skillGap || []).length && <p className="mp-muted">No missing skills identified yet.</p>}
          </div>
        </article>
      </div>

      <article className="mp-card rounded-2xl p-6 bg-[#faf7f0]/85 backdrop-blur-xl border border-[#24231f]/12 shadow-sm hover:border-[#24231f]/20 transition-all">
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
