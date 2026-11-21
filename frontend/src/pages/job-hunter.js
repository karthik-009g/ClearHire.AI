import { useCallback, useEffect, useMemo, useState } from "react";
import dynamic from "next/dynamic";
import ModuleLayout from "../components/ModuleLayout";
import { getPreferences, scrapeJobs, upsertPreferences } from "../api/jobs";
import { listResumeVersions, tailorResume } from "../api/resumes";
import {
  formatPercent,
  getJdContext,
  getResmatContext,
  normalizeSkills,
  parseCsv,
} from "../lib/moduleState";

const ThreeSpatialRadar = dynamic(() => import("../components/ThreeSpatialRadar"), {
  ssr: false,
  loading: () => (
    <div className="w-full h-[580px] rounded-2xl bg-[#faf7f0]/85 backdrop-blur-xl border border-[#24231f]/12 flex flex-col items-center justify-center gap-2 font-mono text-xs text-[#706e68]">
      <span className="w-2.5 h-2.5 rounded-full bg-emerald-600 animate-ping" />
      <span>Initializing 3D Spatial Radar...</span>
    </div>
  ),
});

const NOTICE_PERIOD_OPTIONS = [
  { value: "0", label: "Immediate (0 days)" },
  { value: "15", label: "15 days" },
  { value: "30", label: "30 days (1 month)" },
  { value: "60", label: "60 days (2 months)" },
  { value: "90", label: "90 days (3 months)" },
];

const FALLBACK_REQUISITIONS = [
  {
    id: 1,
    title: "Applied Scientist III - Machine Learning",
    company: "InMobi",
    location: "Bengaluru, Karnataka (Hybrid)",
    ats_provider: "greenhouse",
    score: 96,
    authenticity_score: 99,
    ghosting_risk: "low",
    notice_period: 30,
    description: "Design and implement scalable machine learning models, ad ranking engines, and deep retrieval pipelines handling billions of ad requests daily.",
    url: "https://job-boards.greenhouse.io/inmobi/jobs/8156285",
    fallback_career_url: "https://www.inmobi.com/company/careers/",
    ghosting_signals: {
      positive_signals: ["Direct official ATS portal (Greenhouse)", "Active opening verified", "Clear compensation band"],
      risk_factors: [],
    },
  },
  {
    id: 2,
    title: "Software Development Engineer - Payments",
    company: "Razorpay",
    location: "Bengaluru, Karnataka (On-site)",
    ats_provider: "greenhouse",
    score: 95,
    authenticity_score: 98,
    ghosting_risk: "low",
    notice_period: 30,
    description: "Scale high-concurrency payment routing pipelines handling 10k TPS across India. Microservices in Go/Python.",
    url: "https://razorpay.com/jobs/",
    fallback_career_url: "https://razorpay.com/jobs/",
    ghosting_signals: {
      positive_signals: ["Official Corporate Career Portal", "Direct engineering leadership owned", "Immediate recruiter SLA"],
      risk_factors: [],
    },
  },
  {
    id: 3,
    title: "Fullstack / Backend Software Engineer",
    company: "Groww",
    location: "Bengaluru, Karnataka",
    ats_provider: "greenhouse",
    score: 94,
    authenticity_score: 97,
    ghosting_risk: "low",
    notice_period: 30,
    description: "Build financial investment platforms, stock trading microservices, and mutual fund management infrastructure.",
    url: "https://boards.greenhouse.io/groww",
    fallback_career_url: "https://groww.in/careers",
    ghosting_signals: {
      positive_signals: ["Direct Greenhouse portal", "Active engineering manager contact", "Verified live board"],
      risk_factors: [],
    },
  },
  {
    id: 4,
    title: "Core Infrastructure & Backend Engineer",
    company: "Stripe",
    location: "Bengaluru / Remote",
    ats_provider: "greenhouse",
    score: 93,
    authenticity_score: 96,
    ghosting_risk: "low",
    notice_period: 30,
    description: "Build foundational financial infrastructure, distributed consensus, and payment ledger reliability engines.",
    url: "https://stripe.com/jobs/search?q=engineer",
    fallback_career_url: "https://stripe.com/jobs/search",
    ghosting_signals: {
      positive_signals: ["Greenhouse verified", "High headcount expansion", "72h response SLA"],
      risk_factors: [],
    },
  },
  {
    id: 5,
    title: "AI Systems & Inference Infrastructure Engineer",
    company: "Perplexity AI",
    location: "Remote / Multiple",
    ats_provider: "ashby",
    score: 91,
    authenticity_score: 96,
    ghosting_risk: "low",
    notice_period: 15,
    description: "Build ultra-low-latency model serving, generative answer synthesis pipelines, and real-time citation graphs.",
    url: "https://jobs.ashbyhq.com/perplexity",
    fallback_career_url: "https://jobs.ashbyhq.com/perplexity",
    ghosting_signals: {
      positive_signals: ["Direct Ashby API verified", "Quick interview turnaround", "Live hiring radar"],
      risk_factors: [],
    },
  },
  {
    id: 6,
    title: "Staff Software Engineer - Core Platform",
    company: "CRED",
    location: "Bengaluru, Karnataka",
    ats_provider: "lever",
    score: 90,
    authenticity_score: 95,
    ghosting_risk: "low",
    notice_period: 30,
    description: "Scale high-reliability financial ledger, card payments gateway, and zero-downtime transaction platforms.",
    url: "https://careers.cred.club/",
    fallback_career_url: "https://careers.cred.club/",
    ghosting_signals: {
      positive_signals: ["Direct Corporate Career Hub", "Competitive CTC + ESOPs", "Active requisitions"],
      risk_factors: [],
    },
  },
];

export default function JobHunterPage() {
  const [viewMode, setViewMode] = useState("spatial"); // "spatial" | "list"
  const [showDrawer, setShowDrawer] = useState(false);
  const [resumeContext, setResumeContext] = useState(null);
  const [jdContext, setJdContextState] = useState(null);

  // Search & Filter State
  const [keywordsText, setKeywordsText] = useState("python, fastapi, react, backend, distributed systems");
  const [sourcesText, setSourcesText] = useState("direct_ats, linkedin, naukri");
  const [postedWithinHours, setPostedWithinHours] = useState(72);
  const [directPortalsOnly, setDirectPortalsOnly] = useState(true);
  const [excludeAgencies, setExcludeAgencies] = useState(true);
  const [maxGhostingRisk, setMaxGhostingRisk] = useState("low_only");

  // Indian Job Market & Candidate Preferences
  const [targetCompaniesText, setTargetCompaniesText] = useState("Razorpay, Postman, CRED, Swiggy, Zepto, InMobi, BrowserStack");
  const [noticePeriodDays, setNoticePeriodDays] = useState("30");
  const [servingNotice, setServingNotice] = useState(false);
  const [currentCtcLpa, setCurrentCtcLpa] = useState("");
  const [expectedCtcLpa, setExpectedCtcLpa] = useState("");
  const [workMode, setWorkMode] = useState("any");

  // Status & Results
  const [busy, setBusy] = useState(false);
  const [tailorBusy, setTailorBusy] = useState(false);
  const [prefBusy, setPrefBusy] = useState(false);
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");
  const [results, setResults] = useState([]);
  const [selectedJob, setSelectedJob] = useState(null);
  const [tailorResult, setTailorResult] = useState(null);
  const [appliedJobs, setAppliedJobs] = useState(new Set());
  const [savedJobs, setSavedJobs] = useState(new Set());
  const [cardTilt, setCardTilt] = useState({ rx: 0, ry: 0 });

  useEffect(() => {
    const resume = getResmatContext();
    const jd = getJdContext();
    setResumeContext(resume);
    setJdContextState(jd);

    if (jd?.generatedStack?.length) {
      setKeywordsText(jd.generatedStack.slice(0, 8).join(", "));
    }

    // Load candidate preferences from backend
    getPreferences()
      .then((pref) => {
        if (pref) {
          if (pref.keywords?.length) setKeywordsText(pref.keywords.join(", "));
          if (pref.selected_sources?.length) setSourcesText(pref.selected_sources.join(", "));
          if (pref.target_companies?.length) setTargetCompaniesText(pref.target_companies.join(", "));
          if (pref.direct_portals_only !== undefined) setDirectPortalsOnly(pref.direct_portals_only);
          if (pref.exclude_staffing_agencies !== undefined) setExcludeAgencies(pref.exclude_staffing_agencies);
          if (pref.max_ghosting_risk) setMaxGhostingRisk(pref.max_ghosting_risk);
          if (pref.notice_period_days !== null && pref.notice_period_days !== undefined) {
            setNoticePeriodDays(String(pref.notice_period_days));
          }
          if (pref.serving_notice !== undefined) setServingNotice(pref.serving_notice);
          if (pref.current_ctc_lpa) setCurrentCtcLpa(String(pref.current_ctc_lpa));
          if (pref.expected_ctc_lpa) setExpectedCtcLpa(String(pref.expected_ctc_lpa));
          if (pref.work_mode) setWorkMode(pref.work_mode);
        }
      })
      .catch(() => {});

    // Initial silent search to populate radar
    onSearchSilent();
  }, []);

  const onSearchSilent = async () => {
    try {
      const payload = await scrapeJobs({
        sources: ["direct_ats"],
        keywords: ["engineer", "developer", "backend"],
        direct_portals_only: true,
        exclude_staffing_agencies: true,
        max_ghosting_risk: "low_only",
      });
      const ranked = payload.top_matches?.length ? payload.top_matches : payload.jobs || [];
      if (ranked.length > 0) {
        setResults(ranked);
        setSelectedJob(ranked[0]);
      }
    } catch {
      // Offline fallback
    }
  };

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
        direct_portals_only: directPortalsOnly,
        exclude_staffing_agencies: excludeAgencies,
        max_ghosting_risk: maxGhostingRisk,
      });

      const ranked = payload.top_matches?.length ? payload.top_matches : payload.jobs || [];
      setResults(ranked);
      if (ranked.length > 0) {
        setSelectedJob(ranked[0]);
      }
      setInfo(`3D Orbital Radar locked onto ${ranked.length} authentic direct ATS openings.`);
    } catch (err) {
      setError(err.message || "Job search failed.");
    } finally {
      setBusy(false);
    }
  };

  const onSearchWithKeywords = async (customKeywords) => {
    setKeywordsText(customKeywords);
    setBusy(true);
    setError("");
    setInfo("");

    try {
      const payload = await scrapeJobs({
        sources: parseCsv(sourcesText),
        keywords: parseCsv(customKeywords),
        resume_id: resumeContext?.resumeId || null,
        send_email: false,
        posted_within_hours: Number(postedWithinHours) || 72,
        direct_portals_only: directPortalsOnly,
        exclude_staffing_agencies: excludeAgencies,
        max_ghosting_risk: maxGhostingRisk,
      });

      const ranked = payload.top_matches?.length ? payload.top_matches : payload.jobs || [];
      setResults(ranked);
      if (ranked.length > 0) {
        setSelectedJob(ranked[0]);
      }
      setInfo(`Radar re-calibrated for "${customKeywords}". ${ranked.length} direct requisitions found.`);
    } catch (err) {
      setError(err.message || "Job search failed.");
    } finally {
      setBusy(false);
    }
  };

  const handleSaveToPipeline = (job) => {
    setSavedJobs((prev) => new Set([...prev, job.url || job.id]));
    setInfo(`Saved "${job.title} at ${job.company}" to Pipeline CRM.`);
  };

  const onSavePreferences = async () => {
    setPrefBusy(true);
    setError("");
    setInfo("");

    try {
      await upsertPreferences({
        preferred_email: "candidate@clearhire.ai",
        target_role: keywordsText || "Software Engineer",
        locations: ["Bengaluru", "Hyderabad", "Pune", "Remote"],
        keywords: parseCsv(keywordsText),
        selected_sources: parseCsv(sourcesText),
        target_companies: parseCsv(targetCompaniesText),
        exclude_staffing_agencies: excludeAgencies,
        max_ghosting_risk: maxGhostingRisk,
        direct_portals_only: directPortalsOnly,
        max_post_age_days: 3,
        notice_period_days: Number(noticePeriodDays) || 0,
        serving_notice: servingNotice,
        current_ctc_lpa: currentCtcLpa ? parseFloat(currentCtcLpa) : null,
        expected_ctc_lpa: expectedCtcLpa ? parseFloat(expectedCtcLpa) : null,
        work_mode: workMode,
        auto_schedule_enabled: true,
        schedule_time: "08:30",
        schedule_timezone: "Asia/Kolkata",
        auto_scrape_on_login: true,
        auto_email_after_scrape: false,
      });
      setInfo("Profile and notice period preferences updated.");
      setShowDrawer(false);
    } catch (err) {
      setError(err.message || "Failed to save preferences.");
    } finally {
      setPrefBusy(false);
    }
  };

  const onTailorForJob = async (job) => {
    if (!resumeContext?.resumeId) {
      setError("Please upload your master resume in ResMat.ai first.");
      return;
    }

    setError("");
    setInfo("");
    setTailorBusy(true);

    const jdText = [
      `Role: ${job.title} at ${job.company}`,
      `Location: ${job.location || "India"}`,
      `ATS / Source: ${job.ats_provider || job.source}`,
      `Description: ${job.description || ""}`,
    ].join("\n");

    try {
      const payload = await tailorResume({
        resume_id: resumeContext.resumeId,
        source_version_no: 1,
        jd_text: jdText,
        role: job.title,
        company: job.company,
        source: `clearhire-${job.ats_provider || job.source}`,
        include_cover_letter: true,
      });

      setTailorResult(payload);
      setInfo(`1-Page ATS Resume v${payload.version_no} tailored specifically for ${job.company}.`);
    } catch (err) {
      setError(err.message || "Tailor agent failed.");
    } finally {
      setTailorBusy(false);
    }
  };

  const handleApply = (job) => {
    if (!job) return;
    const targetUrl = job.is_expired ? (job.fallback_career_url || job.url) : job.url;
    setAppliedJobs((prev) => new Set([...prev, job.url || targetUrl]));
    if (job.is_expired) {
      setInfo(`Requisition closed by employer — Redirecting to verified official career portal for ${job.company}.`);
    } else {
      setInfo(`Opening verified requisition for ${job.title} at ${job.company}...`);
    }
    window.open(targetUrl, "_blank", "noopener,noreferrer");
  };

  const handleOpenCareerPortal = (job) => {
    if (!job) return;
    const portalUrl = job.fallback_career_url || `https://${(job.company || "").toLowerCase().replace(/[^a-z0-9]/g, "")}.com/careers`;
    window.open(portalUrl, "_blank", "noopener,noreferrer");
    setInfo(`Opening verified corporate career hub for ${job.company}.`);
  };

  // Card 3D Tilt calculation (ClearHire 3D Tilt Dynamics)
  const handleCardMouseMove = (e) => {
    const card = e.currentTarget;
    const rect = card.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const rx = ((y - rect.height / 2) / (rect.height / 2)) * -6;
    const ry = ((x - rect.width / 2) / (rect.width / 2)) * 6;
    setCardTilt({ rx, ry });
  };

  const handleCardMouseLeave = () => {
    setCardTilt({ rx: 0, ry: 0 });
  };

  const displayJobs = useMemo(() => {
    return results.length > 0 ? results : FALLBACK_REQUISITIONS;
  }, [results]);

  const handleSelectJob = useCallback((job) => {
    setSelectedJob(job);
  }, []);

  const handleHoverJob = useCallback(() => {}, []);

  const activeJob = selectedJob || displayJobs[0];

  return (
    <ModuleLayout
      title="Direct Corporate ATS Requisition Radar"
      subtitle="Verified Requisitions directly from Greenhouse, Lever, Ashby, and Workday Core · 0% Aggregator Detours"
    >
      {/* 1. Top Clean Control Island (Editorial Glass HUD) */}
      <section className="relative z-10 w-full mb-6">
        <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-2xl bg-[#faf7f0]/85 backdrop-blur-xl border border-[#24231f]/12 shadow-sm">
          {/* Search Input Island */}
          <div className="flex-1 min-w-[280px] flex items-center gap-3 bg-white/80 px-4 py-2.5 rounded-xl border border-[#24231f]/15 focus-within:border-[#5369d9]/50 transition-all">
            <span className="text-[#5369d9] text-sm">🔍</span>
            <input
              type="text"
              value={keywordsText}
              onChange={(e) => setKeywordsText(e.target.value)}
              placeholder="Keywords / Target Stack (e.g. Python, FastAPI, React, Distributed Systems)..."
              className="w-full bg-transparent border-0 outline-none text-[#24231f] text-xs font-mono placeholder:text-[#5369d9]/30"
              onKeyDown={(e) => e.key === "Enter" && onSearch()}
            />
          </div>

          {/* Quick Filter Pills */}
          <div className="flex items-center gap-2 flex-wrap">
            <button
              type="button"
              onClick={() => setDirectPortalsOnly(!directPortalsOnly)}
              className={`font-mono text-xs px-3 py-2 rounded-xl border transition-all flex items-center gap-1.5 ${
                directPortalsOnly
                  ? "bg-[#5369d9]/10 border-[#5369d9]/50 text-[#5369d9]"
                  : "bg-white/50 border-[#24231f]/10 text-[#706e68] hover:text-[#24231f] hover:bg-white"
              }`}
            >
              <span>🟢</span> Direct ATS
            </button>

            <button
              type="button"
              onClick={() => setExcludeAgencies(!excludeAgencies)}
              className={`font-mono text-xs px-3 py-2 rounded-xl border transition-all flex items-center gap-1.5 ${
                excludeAgencies
                  ? "bg-[#5369d9]/10 border-[#5369d9]/50 text-[#5369d9]"
                  : "bg-white/50 border-[#24231f]/10 text-[#706e68] hover:text-[#24231f] hover:bg-white"
              }`}
            >
              <span>🛡️</span> Anti-Ghosting
            </button>

            <button
              type="button"
              onClick={() => setShowDrawer(true)}
              className="font-mono text-xs px-3 py-2 rounded-xl border border-[#24231f]/12 shadow-sm bg-white/70 text-[#5369d9] hover:bg-[#5369d9]/8 transition-all flex items-center gap-1.5"
            >
              <span>⚙️</span> India CTC & Notice
            </button>

            <button
              type="button"
              onClick={onSearch}
              disabled={busy}
              className="font-mono text-xs px-5 py-2 rounded-xl font-bold bg-[#24231f] text-white hover:bg-[#3d3a33] active:scale-95 transition-all shadow-[0_4px_16px_rgba(36,35,31,0.12)] disabled:opacity-50"
            >
              {busy ? "Scanning Space..." : "Scan Radar →"}
            </button>
          </div>

          {/* Quick Preset Stack Chips */}
          <div className="flex items-center gap-2 pt-2 border-t border-[#24231f]/8 w-full overflow-x-auto no-scrollbar">
            <span className="font-mono text-[10px] uppercase text-[#706e68] whitespace-nowrap">Quick Stack Presets:</span>
            {[
              { label: "🔥 Razorpay / Fintech Backend", kw: "python, fastapi, backend, distributed systems" },
              { label: "🚀 AI Engineer / Agents", kw: "python, llm, embeddings, rag, agents" },
              { label: "⚡ Immediate Notice (0-15d)", kw: "python, postgresql, docker, aws" },
              { label: "📍 Bengaluru Remote", kw: "fullstack, react, typescript, node" },
            ].map((preset) => (
              <button
                key={preset.label}
                type="button"
                onClick={() => onSearchWithKeywords(preset.kw)}
                className="font-mono text-[10px] px-2.5 py-1 rounded-full bg-white border border-[#24231f]/10 text-[#525048] hover:text-[#5369d9] hover:border-[#5369d9]/40 active:scale-95 transition-all whitespace-nowrap shadow-xs"
              >
                {preset.label}
              </button>
            ))}
          </div>
        </div>

        {/* Status Alerts */}
        {error && (
          <div className="mt-3 p-3 rounded-xl bg-red-50 border border-red-200 text-[#b91c1c] text-xs font-mono font-medium flex items-center gap-2">
            <span>⚠️</span> {error}
          </div>
        )}
        {info && (
          <div className="mt-3 p-3 rounded-xl bg-[#5369d9]/8 border border-[#5369d9]/30 text-[#5369d9] text-xs font-mono flex items-center gap-2">
            <span>✨</span> {info}
          </div>
        )}
      </section>

      {/* 2. Direct Requisition Radar Target Console (3D Spatial Radar / 2D Grid) */}
      <section className="relative z-0 w-full mb-8 rounded-2xl p-6 bg-[#faf7f0]/85 backdrop-blur-xl border border-[#24231f]/12 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-4 pb-4 mb-4 border-b border-[#24231f]/10">
          <div className="flex items-center gap-3">
            <span className="w-2.5 h-2.5 rounded-full bg-[#10b981] animate-pulse" />
            <div>
              <h3 className="font-mono text-xs font-bold uppercase tracking-wider text-[#24231f]">
                DIRECT REQUISITION RADAR TARGETS
              </h3>
              <p className="text-[11px] font-mono text-[#706e68]">
                {displayJobs.length} active requisitions indexed • Ghosting SLA &lt;72h verified
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 font-mono text-[11px] flex-wrap">
            <span className="px-2.5 py-1 rounded-full bg-[#10b981]/10 border border-[#10b981]/30 text-[#15803d] font-bold">
              ✓ Direct ATS Only
            </span>
            <div className="flex items-center bg-[#faf7f0] border border-[#24231f]/12 rounded-xl p-1 shadow-xs">
              <button
                type="button"
                onClick={() => setViewMode("spatial")}
                className={`font-mono text-xs px-3 py-1.5 rounded-lg transition-all cursor-pointer ${
                  viewMode === "spatial"
                    ? "bg-[#24231f] text-[#faf7f0] font-semibold shadow-xs"
                    : "text-[#706e68] hover:text-[#24231f]"
                }`}
              >
                🌌 3D Spatial Radar
              </button>
              <button
                type="button"
                onClick={() => setViewMode("grid")}
                className={`font-mono text-xs px-3 py-1.5 rounded-lg transition-all cursor-pointer ${
                  viewMode === "grid"
                    ? "bg-[#24231f] text-[#faf7f0] font-semibold shadow-xs"
                    : "text-[#706e68] hover:text-[#24231f]"
                }`}
              >
                📋 Requisition Grid
              </button>
            </div>
          </div>
        </div>

        {/* 3D Spatial Radar vs 2D Target Nodes Grid */}
        {viewMode === "spatial" ? (
          <ThreeSpatialRadar
            jobs={displayJobs}
            selectedJobId={activeJob?.id}
            onSelectJob={handleSelectJob}
            onHoverJob={handleHoverJob}
          />
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
            {displayJobs.map((job) => {
              const isSelected = activeJob?.id === job.id;
              return (
                <button
                  key={job.id}
                  type="button"
                  onClick={() => setSelectedJob(job)}
                  className={`text-left p-3.5 rounded-xl border transition-all duration-150 flex flex-col justify-between gap-2.5 ${
                    isSelected
                      ? "bg-[#5369d9]/10 border-[#5369d9] shadow-[0_0_15px_rgba(83,105,217,0.18)] ring-2 ring-[#5369d9]/30"
                      : "bg-[#faf7f0] border-[#24231f]/10 hover:border-[#5369d9]/40 hover:bg-white"
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <span className="font-mono text-[11px] font-bold text-[#5369d9] uppercase tracking-wider">
                      {job.company}
                    </span>
                    <span
                      className={`font-mono text-[10px] px-2 py-0.5 rounded-full font-bold ${
                        (job.score || 90) >= 90
                          ? "bg-[#10b981]/15 text-[#15803d] border border-[#10b981]/30"
                          : "bg-amber-500/15 text-amber-700 border border-amber-500/30"
                      }`}
                    >
                      {Math.round(job.score || 90)}% Match
                    </span>
                  </div>

                  <div>
                    <h4 className="font-serif text-sm font-semibold text-[#24231f] line-clamp-1">
                      {job.title}
                    </h4>
                    <p className="font-mono text-[10px] text-[#706e68] mt-0.5">
                      📍 {job.location || "Bengaluru"} • {job.ats_provider?.toUpperCase() || "DIRECT"}
                    </p>
                  </div>

                  <div className="flex items-center justify-between pt-2 border-t border-[#24231f]/8 font-mono text-[10px]">
                    <span className="text-[#10b981] font-semibold flex items-center gap-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-[#10b981]" />
                      {job.ghosting_risk === "low" ? "<72h Response" : "Verified Direct"}
                    </span>
                    <span className="text-[#5369d9] font-bold">
                      {isSelected ? "ACTIVE ◉" : "Inspect →"}
                    </span>
                  </div>
                </button>
              );
            })}
          </div>
        )}
      </section>

      {/* 3. High-End 3D Gyroscope Glass Card Inspector */}
      <section className="relative z-10 w-full grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Active 3D Job Capsule Inspector (Interactive Tilt Physics) */}
        <div
          className="lg:col-span-2 rounded-2xl p-7 bg-[#faf7f0]/85 backdrop-blur-xl border border-[#24231f]/12 shadow-sm transition-transform duration-100 ease-out text-[#24231f]"
          style={{
            transform: `perspective(1000px) rotateX(${cardTilt.rx}deg) rotateY(${cardTilt.ry}deg)`,
          }}
          onMouseMove={handleCardMouseMove}
          onMouseLeave={handleCardMouseLeave}
        >
          {/* Header Row */}
          <div className="flex flex-wrap items-start justify-between gap-3 mb-4">
            <div>
              <span className="font-mono text-xs uppercase tracking-widest text-[#5369d9] font-bold">
                {activeJob.company} • DIRECT {activeJob.ats_provider ? activeJob.ats_provider.toUpperCase() : "ATS"}
              </span>
              <h3 className="font-serif text-2xl font-semibold text-[#24231f] mt-1 tracking-tight">
                {activeJob.title}
              </h3>
              <p className="text-xs font-mono text-[#706e68] mt-1">
                📍 {activeJob.location || "Bengaluru, India"} • Source: Authentic Career Portal
              </p>
            </div>

            <div className="flex flex-col items-end gap-1.5">
              <span
                className="font-mono text-xs px-3 py-1 rounded-full font-bold border"
                style={{
                  backgroundColor:
                    activeJob.ghosting_risk === "low"
                      ? "rgba(21, 128, 61, 0.1)"
                      : "rgba(180, 83, 9, 0.1)",
                  borderColor:
                    activeJob.ghosting_risk === "low"
                      ? "rgba(21, 128, 61, 0.25)"
                      : "rgba(180, 83, 9, 0.25)",
                  color: activeJob.ghosting_risk === "low" ? "#15803d" : "#b45309",
                }}
              >
                {activeJob.ghosting_risk === "low" ? "🟢 Low Ghosting Risk" : "🟡 Medium Risk"} ({activeJob.authenticity_score || 95}%)
              </span>
              <span className="font-mono text-[10px] text-[#5369d9]/70">
                Match Score: {Math.round(activeJob.score || 92)}%
              </span>
              <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] font-mono font-medium border ${activeJob.is_expired ? "bg-amber-500/10 border-amber-500/25 text-amber-800" : "bg-emerald-500/10 border-emerald-500/25 text-emerald-800"}`}>
                <span className={`w-2 h-2 rounded-full ${activeJob.is_expired ? "bg-amber-500" : "bg-emerald-500 animate-pulse"}`} />
                {activeJob.is_expired ? "⚠ Closed by Employer (Portal Fallback Active)" : "● Verified Active Requisition"}
              </span>
            </div>
          </div>

          {/* Indian Market Metrics Strip */}
          <div className="grid grid-cols-3 gap-3 p-3 rounded-xl bg-white/60 backdrop-blur-md border border-[#24231f]/10 font-mono text-xs mb-5 shadow-xs">
            <div>
              <span className="text-[#5369d9]/50 block text-[10px] uppercase">Notice Period</span>
              <strong className="text-[#24231f]">≤ {noticePeriodDays} Days</strong>
            </div>
            <div>
              <span className="text-[#5369d9]/50 block text-[10px] uppercase">Target CTC</span>
              <strong className="text-[#24231f]">₹ {expectedCtcLpa || "20-35"} LPA</strong>
            </div>
            <div>
              <span className="text-[#5369d9]/50 block text-[10px] uppercase">Autofill Status</span>
              <strong className="text-[#5369d9]">✨ Extension Ready</strong>
            </div>
          </div>

          {/* Role Snippet */}
          <div className="mb-6">
            <h4 className="font-mono text-xs text-[#5369d9]/70 uppercase tracking-wider mb-2">Role Overview & Tech Stack</h4>
            <p className="text-sm text-[#525048] leading-relaxed line-clamp-4">
              {activeJob.description || "Direct engineering role verified at official company careers portal. Requires expertise in distributed backend systems, Python, FastAPI, relational databases, and high-concurrency microservices."}
            </p>
          </div>

          {/* Actions Bar */}
          <div className="flex flex-wrap items-center gap-2.5 pt-4 border-t border-[#24231f]/10">
            <button
              type="button"
              onClick={() => handleApply(activeJob)}
              className="font-mono text-xs px-5 py-2.5 rounded-xl font-bold bg-[#24231f] text-white hover:bg-[#3d3a33] active:scale-95 transition-all shadow-md flex items-center gap-1.5"
            >
              <span>1-Click Direct ATS Apply</span>
              <span>→</span>
            </button>

            <button
              type="button"
              onClick={() => handleOpenCareerPortal(activeJob)}
              className="font-mono text-xs px-4 py-2.5 rounded-xl border border-[#24231f]/20 bg-white text-[#24231f] hover:bg-[#faf7f0] active:scale-95 transition-all flex items-center gap-1.5 font-semibold"
              title="Open official corporate career hub (verified fallback)"
            >
              <span>🏢</span>
              <span>Company Career Hub ↗</span>
            </button>

            <button
              type="button"
              onClick={() => onTailorForJob(activeJob)}
              disabled={tailorBusy}
              className="font-mono text-xs px-4 py-2.5 rounded-xl border border-[#5369d9]/30 bg-[#5369d9]/10 text-[#5369d9] hover:bg-[#5369d9]/20 active:scale-95 transition-all disabled:opacity-50 flex items-center gap-1.5 font-semibold"
            >
              <span>📄</span>
              <span>{tailorBusy ? "Tailoring..." : "Tailor 1-Page ATS PDF"}</span>
            </button>

            <button
              type="button"
              onClick={() => handleSaveToPipeline(activeJob)}
              className="font-mono text-xs px-4 py-2.5 rounded-xl border border-[#24231f]/15 bg-white text-[#24231f] hover:bg-[#faf7f0] active:scale-95 transition-all flex items-center gap-1.5 font-semibold shadow-xs"
            >
              <span>📋</span>
              <span>{savedJobs.has(activeJob.url || activeJob.id) ? "Saved in CRM ✓" : "Save to Pipeline"}</span>
            </button>

            {appliedJobs.has(activeJob.url) && (
              <span className="font-mono text-xs text-[#15803d] font-semibold flex items-center gap-1 ml-auto">
                ✓ Applied & Tracked
              </span>
            )}
          </div>
        </div>

        {/* Right: Radar Node Roster (Quick Switcher) */}
        <div className="rounded-2xl p-5 bg-[#faf7f0]/85 backdrop-blur-xl border border-[#24231f]/12 shadow-sm flex flex-col">
          <div className="flex items-center justify-between pb-3 border-b border-[#24231f]/10 mb-3">
            <h4 className="font-mono text-xs font-bold text-[#24231f] uppercase tracking-wider">
              Orbital Node Roster
            </h4>
            <span className="font-mono text-[10px] text-[#5369d9] bg-[#5369d9]/8 px-2 py-0.5 rounded-full">
              {results.length} Available
            </span>
          </div>

          <div className="flex-1 overflow-y-auto max-h-[380px] space-y-2 pr-1">
            {results.map((job, idx) => {
              const isSelected = activeJob.id === job.id;
              return (
                <div
                  key={job.id || idx}
                  onClick={() => setSelectedJob(job)}
                  className={`p-3 rounded-xl border cursor-pointer transition-all ${
                    isSelected
                      ? "bg-[#5369d9]/10 border-[#5369d9]/50 shadow-[0_4px_16px_rgba(83,105,217,0.15)]"
                      : "bg-white border-[#24231f]/8 hover:border-[#5369d9]/30 hover:bg-[#5369d9]/5"
                  }`}
                >
                  <div className="flex items-center justify-between gap-1 mb-1">
                    <span className="font-mono text-[11px] font-bold text-[#24231f] truncate">
                      {job.company}
                    </span>
                    <span className="font-mono text-[10px] text-[#5369d9]">
                      {Math.round(job.score || 90)}%
                    </span>
                  </div>
                  <p className="text-xs text-[#706e68] truncate">{job.title}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* 4. Slide-Over Profile & India Settings Drawer */}
      {showDrawer && (
        <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-sm animate-fade-in">
          <div className="w-full max-w-md h-full bg-[#faf7f0] border-l border-[#24231f]/15 p-6 overflow-y-auto shadow-2xl flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between pb-4 border-b border-[#24231f]/15 mb-5">
                <div>
                  <h3 className="font-serif text-lg font-semibold text-[#24231f]">Indian Market Profile</h3>
                  <p className="text-xs text-[#706e68] font-mono">Notice Period, CTC & Company Filters</p>
                </div>
                <button
                  type="button"
                  onClick={() => setShowDrawer(false)}
                  className="w-8 h-8 rounded-lg bg-[#eee9df] text-[#24231f] hover:opacity-80 flex items-center justify-center font-mono text-sm"
                >
                  ✕
                </button>
              </div>

              <div className="space-y-4 font-mono text-xs">
                <div>
                  <label className="block text-[#5369d9]/70 mb-1.5 uppercase text-[10px]">
                    Notice Period
                  </label>
                  <select
                    value={noticePeriodDays}
                    onChange={(e) => setNoticePeriodDays(e.target.value)}
                    className="w-full bg-white border border-[#24231f]/12 shadow-sm rounded-xl px-3 py-2 text-[#24231f] bg-white outline-none"
                  >
                    {NOTICE_PERIOD_OPTIONS.map((opt) => (
                      <option key={opt.value} value={opt.value} className="bg-white">
                        {opt.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-[#5369d9]/70 mb-1.5 uppercase text-[10px]">
                      Current CTC (₹ LPA)
                    </label>
                    <input
                      type="number"
                      value={currentCtcLpa}
                      onChange={(e) => setCurrentCtcLpa(e.target.value)}
                      placeholder="e.g. 18"
                      className="w-full bg-white border border-[#24231f]/12 shadow-sm rounded-xl px-3 py-2 text-[#24231f] bg-white outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-[#5369d9]/70 mb-1.5 uppercase text-[10px]">
                      Expected CTC (₹ LPA)
                    </label>
                    <input
                      type="number"
                      value={expectedCtcLpa}
                      onChange={(e) => setExpectedCtcLpa(e.target.value)}
                      placeholder="e.g. 28"
                      className="w-full bg-white border border-[#24231f]/12 shadow-sm rounded-xl px-3 py-2 text-[#24231f] bg-white outline-none"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-[#5369d9]/70 mb-1.5 uppercase text-[10px]">
                    Target Tech Unicorns (CSV)
                  </label>
                  <input
                    type="text"
                    value={targetCompaniesText}
                    onChange={(e) => setTargetCompaniesText(e.target.value)}
                    placeholder="Razorpay, Postman, CRED, Zepto..."
                    className="w-full bg-white border border-[#24231f]/12 shadow-sm rounded-xl px-3 py-2 text-[#24231f] bg-white outline-none"
                  />
                </div>

                <div>
                  <label className="block text-[#5369d9]/70 mb-1.5 uppercase text-[10px]">
                    Work Mode Preference
                  </label>
                  <select
                    value={workMode}
                    onChange={(e) => setWorkMode(e.target.value)}
                    className="w-full bg-white border border-[#24231f]/12 shadow-sm rounded-xl px-3 py-2 text-[#24231f] bg-white outline-none"
                  >
                    <option value="any" className="bg-white">Any (Remote / Hybrid / On-site)</option>
                    <option value="remote" className="bg-white">Strict Remote</option>
                    <option value="hybrid" className="bg-white">Hybrid</option>
                  </select>
                </div>
              </div>
            </div>

            <div className="pt-5 border-t border-[#24231f]/15 flex items-center gap-3">
              <button
                type="button"
                onClick={onSavePreferences}
                disabled={prefBusy}
                className="w-full py-2.5 rounded-xl font-mono text-xs font-bold bg-[#5369d9] text-white hover:bg-[#4052b3] transition-all disabled:opacity-50 shadow-sm"
              >
                {prefBusy ? "Saving..." : "Save Preferences"}
              </button>
            </div>
          </div>
        </div>
      )}
    </ModuleLayout>
  );
}
