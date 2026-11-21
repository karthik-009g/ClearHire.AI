import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/router";
import ModuleLayout from "../components/ModuleLayout";
import { getMe } from "../api/auth";
import { clearAuthToken, getStoredAuthToken, setAuthToken } from "../api/client";
import { getJdContext, getResmatContext } from "../lib/moduleState";

export default function HomePage() {
  const router = useRouter();
  const [user, setUser] = useState(null);
  const [resumeContext, setResumeContext] = useState(null);
  const [jdContext, setJdContextState] = useState(null);

  // Interactive micro-tools in workspace
  const [dormancyDays, setDormancyDays] = useState(14);
  const [pipelineFilter, setPipelineFilter] = useState("Interviewing");
  const [briefingChannel, setBriefingChannel] = useState("telegram");

  useEffect(() => {
    let active = true;
    const initSession = async () => {
      const token = getStoredAuthToken();
      if (!token) {
        if (active) router.replace("/login");
        return;
      }
      try {
        setAuthToken(token);
        const me = await getMe();
        if (active) {
          setUser(me);
          setResumeContext(getResmatContext());
          setJdContextState(getJdContext());
        }
      } catch {
        clearAuthToken();
        if (active) router.replace("/login");
      }
    };
    initSession();

    return () => {
      active = false;
    };
  }, [router]);

  const ghostRisk = Math.min(96, Math.max(2, Math.round(dormancyDays * 2.8)));
  const fallbackRoutes = dormancyDays >= 14 ? 3 : dormancyDays >= 7 ? 2 : 1;

  return (
    <ModuleLayout
      title="ClearHire Candidate Workspace"
      subtitle="A more human way to hire. Every verified requisition, application status, and ATS screening context in one connected thread."
    >
      <div className="space-y-8">
        {/* Top Hero Telemetry Strip */}
        <section className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="p-5 rounded-2xl bg-[#faf7f0]/85 backdrop-blur-xl border border-[#24231f]/12 shadow-sm hover:border-[#24231f]/25 hover:shadow-md transition-all">
            <span className="font-mono text-[9px] uppercase tracking-wider text-[#706e68] block mb-1">
              Direct Corporate ATS
            </span>
            <strong className="font-serif text-2xl text-[#24231f] block">
              40+ Partners
            </strong>
            <p className="text-[11px] font-mono text-[#5369d9] mt-1.5 mb-0">
              0% middlemen · 100% direct
            </p>
          </div>

          <div className="p-5 rounded-2xl bg-[#faf7f0]/85 backdrop-blur-xl border border-[#24231f]/12 shadow-sm hover:border-[#24231f]/25 hover:shadow-md transition-all">
            <span className="font-mono text-[9px] uppercase tracking-wider text-[#706e68] block mb-1">
              Anti-Ghosting SLA
            </span>
            <strong className="font-serif text-2xl text-[#24231f] block">
              14-Day SLA
            </strong>
            <p className="text-[11px] font-mono text-[#bd7652] mt-1.5 mb-0">
              95% grounded telemetry
            </p>
          </div>

          <div className="p-5 rounded-2xl bg-[#faf7f0]/85 backdrop-blur-xl border border-[#24231f]/12 shadow-sm hover:border-[#24231f]/25 hover:shadow-md transition-all">
            <span className="font-mono text-[9px] uppercase tracking-wider text-[#706e68] block mb-1">
              1-Page ATS Resume
            </span>
            <strong className="font-serif text-2xl text-[#24231f] block">
              99.4% Pass
            </strong>
            <p className="text-[11px] font-mono text-[#5369d9] mt-1.5 mb-0">
              Zero page overflow budget
            </p>
          </div>

          <div className="p-5 rounded-2xl bg-[#faf7f0]/85 backdrop-blur-xl border border-[#24231f]/12 shadow-sm hover:border-[#24231f]/25 hover:shadow-md transition-all">
            <span className="font-mono text-[9px] uppercase tracking-wider text-[#706e68] block mb-1">
              Morning Intelligence
            </span>
            <strong className="font-serif text-2xl text-[#24231f] block">
              08:30 IST
            </strong>
            <p className="text-[11px] font-mono text-emerald-700 mt-1.5 mb-0">
              Telegram · WhatsApp · HTML
            </p>
          </div>
        </section>

        {/* 6 Narrative Feature Chapters Grid */}
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-serif text-2xl font-medium text-[#24231f] m-0">
              Core Capabilities &amp; Workflows
            </h2>
            <span className="font-mono text-xs text-[#706e68]">
              6 Integrated Modules · 1 Unified Database
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* 01: Direct Corporate ATS Ingestion */}
            <article className="p-6 rounded-2xl bg-[#faf7f0]/85 backdrop-blur-xl border border-[#24231f]/12 shadow-sm hover:shadow-md transition-all flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="font-mono text-[10px] text-[#5369d9] font-bold uppercase tracking-wider">
                    Chapter 01 / Ingestion
                  </span>
                  <span className="font-mono text-[9px] px-2 py-0.5 rounded-full bg-[#5369d9]/10 text-[#5369d9] border border-[#5369d9]/20">
                    Live Feed
                  </span>
                </div>
                <h3 className="font-serif text-xl font-medium text-[#24231f] mb-2 m-0">
                  Direct Corporate ATS Engine
                </h3>
                <p className="text-xs text-[#5d5b55] leading-relaxed mb-4">
                  Connects directly to Greenhouse, Lever, Ashby, and Workday enterprise systems, routing verified requisitions without third-party aggregator noise.
                </p>
                <div className="flex flex-wrap gap-1.5 mb-4">
                  <span className="font-mono text-[9px] px-2 py-1 rounded bg-white border border-[#24231f]/10 text-[#5e5b55]">Greenhouse</span>
                  <span className="font-mono text-[9px] px-2 py-1 rounded bg-white border border-[#24231f]/10 text-[#5e5b55]">Lever</span>
                  <span className="font-mono text-[9px] px-2 py-1 rounded bg-white border border-[#24231f]/10 text-[#5e5b55]">Ashby</span>
                  <span className="font-mono text-[9px] px-2 py-1 rounded bg-white border border-[#24231f]/10 text-[#5e5b55]">Workday</span>
                </div>
              </div>
              <Link
                href="/job-hunter"
                className="inline-flex items-center justify-between px-4 py-2.5 rounded-xl bg-[#24231f] text-white text-xs font-semibold hover:bg-[#3d3b35] transition-all no-underline"
              >
                <span>Browse Direct Requisitions</span>
                <span>→</span>
              </Link>
            </article>

            {/* 02: Deterministic Anti-Ghosting */}
            <article className="p-6 rounded-2xl bg-[#faf7f0]/85 backdrop-blur-xl border border-[#24231f]/12 shadow-sm hover:shadow-md transition-all flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="font-mono text-[10px] text-[#bd7652] font-bold uppercase tracking-wider">
                    Chapter 02 / Telemetry
                  </span>
                  <span className="font-mono text-[9px] px-2 py-0.5 rounded-full bg-[#bd7652]/10 text-[#985b39] border border-[#bd7652]/20">
                    14-Day SLA
                  </span>
                </div>
                <h3 className="font-serif text-xl font-medium text-[#24231f] mb-2 m-0">
                  Deterministic Anti-Ghosting
                </h3>
                <p className="text-xs text-[#5d5b55] leading-relaxed mb-3">
                  Responsiveness telemetry spots dormant roles early. When an employer goes quiet, ClearHire automatically calculates fallback alternatives.
                </p>
                {/* Mini simulator */}
                <div className="p-3 rounded-xl bg-white/60 backdrop-blur-md border border-[#24231f]/10 mb-4 shadow-xs">
                  <div className="flex justify-between items-center text-[10px] font-mono text-[#706e68] mb-1.5">
                    <span>Inactivity: {dormancyDays} days</span>
                    <span className="text-[#5369d9] font-bold">{ghostRisk}% risk · {fallbackRoutes} routes</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="30"
                    value={dormancyDays}
                    onChange={(e) => setDormancyDays(Number(e.target.value))}
                    className="w-full accent-[#5369d9]"
                  />
                </div>
              </div>
              <Link
                href="/applications"
                className="inline-flex items-center justify-between px-4 py-2.5 rounded-xl bg-white border border-[#24231f]/15 text-[#24231f] text-xs font-semibold hover:border-[#bd7652] transition-all no-underline"
              >
                <span>Inspect Pipeline Health</span>
                <span>→</span>
              </Link>
            </article>

            {/* 03: Strict 1-Page ATS Resume Synthesizer */}
            <article className="p-6 rounded-2xl bg-[#faf7f0]/85 backdrop-blur-xl border border-[#24231f]/12 shadow-sm hover:shadow-md transition-all flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="font-mono text-[10px] text-[#5369d9] font-bold uppercase tracking-wider">
                    Chapter 03 / Synthesis
                  </span>
                  <span className="font-mono text-[9px] px-2 py-0.5 rounded-full bg-[#5369d9]/10 text-[#5369d9] border border-[#5369d9]/20">
                    99.4% ATS Pass
                  </span>
                </div>
                <h3 className="font-serif text-xl font-medium text-[#24231f] mb-2 m-0">
                  Strict 1-Page Resume Synthesizer
                </h3>
                <p className="text-xs text-[#5d5b55] leading-relaxed mb-4">
                  A layout-aware resume compiler tunes typography scale and line breaks to produce a guaranteed one-page PDF tailored to candidate telemetry.
                </p>
                <div className="p-3 rounded-xl bg-white/60 backdrop-blur-md border border-[#24231f]/10 mb-4 shadow-xs font-mono text-[10px] space-y-1 text-[#65625c]">
                  <div>✓ Strict 1-page budget constraint</div>
                  <div>✓ Layout density switcher (9.5pt vs 11pt)</div>
                  <div>✓ Zero text overflow or truncation</div>
                </div>
              </div>
              <Link
                href="/resmat-ai"
                className="inline-flex items-center justify-between px-4 py-2.5 rounded-xl bg-[#24231f] text-white text-xs font-semibold hover:bg-[#3d3b35] transition-all no-underline"
              >
                <span>Synthesize 1-Page Resume</span>
                <span>→</span>
              </Link>
            </article>

            {/* 04: Candidate Pipeline CRM */}
            <article className="p-6 rounded-2xl bg-[#faf7f0]/85 backdrop-blur-xl border border-[#24231f]/12 shadow-sm hover:shadow-md transition-all flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="font-mono text-[10px] text-[#d97861] font-bold uppercase tracking-wider">
                    Chapter 04 / Pipeline
                  </span>
                  <span className="font-mono text-[9px] px-2 py-0.5 rounded-full bg-[#d97861]/10 text-[#d97861] border border-[#d97861]/20">
                    7 CRM Stages
                  </span>
                </div>
                <h3 className="font-serif text-xl font-medium text-[#24231f] mb-2 m-0">
                  Autonomous 7-Stage Pipeline
                </h3>
                <p className="text-xs text-[#5d5b55] leading-relaxed mb-3">
                  Track candidates from discovery through offer execution with saved notes, recruiter follow-ups, and interview loop context in one thread.
                </p>
                <div className="flex flex-wrap gap-1 mb-4">
                  {["Saved", "Screened", "Applied", "Interviewing", "Offer"].map((stg) => (
                    <button
                      key={stg}
                      type="button"
                      onClick={() => setPipelineFilter(stg)}
                      className={`font-mono text-[9px] px-2 py-1 rounded transition-colors ${
                        pipelineFilter === stg
                          ? "bg-[#5369d9] text-white"
                          : "bg-white border border-[#24231f]/10 text-[#5e5b55]"
                      }`}
                    >
                      {stg}
                    </button>
                  ))}
                </div>
              </div>
              <Link
                href="/applications"
                className="inline-flex items-center justify-between px-4 py-2.5 rounded-xl bg-white border border-[#24231f]/15 text-[#24231f] text-xs font-semibold hover:border-[#5369d9] transition-all no-underline"
              >
                <span>Open Kanban CRM</span>
                <span>→</span>
              </Link>
            </article>

            {/* 05: Multi-Channel Morning Briefing */}
            <article className="p-6 rounded-2xl bg-[#faf7f0]/85 backdrop-blur-xl border border-[#24231f]/12 shadow-sm hover:shadow-md transition-all flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="font-mono text-[10px] text-[#9673cb] font-bold uppercase tracking-wider">
                    Chapter 05 / Intelligence
                  </span>
                  <span className="font-mono text-[9px] px-2 py-0.5 rounded-full bg-[#9673cb]/10 text-[#9673cb] border border-[#9673cb]/20">
                    08:30 Daily
                  </span>
                </div>
                <h3 className="font-serif text-xl font-medium text-[#24231f] mb-2 m-0">
                  Morning Intelligence Briefing
                </h3>
                <p className="text-xs text-[#5d5b55] leading-relaxed mb-3">
                  Scheduled daily report surfacing verified engineering openings, pipeline progress, dormant role alternatives, and LPA market compensation.
                </p>
                <div className="flex gap-1.5 mb-4">
                  {["telegram", "whatsapp", "html"].map((ch) => (
                    <button
                      key={ch}
                      type="button"
                      onClick={() => setBriefingChannel(ch)}
                      className={`font-mono text-[9px] px-2.5 py-1 rounded-full uppercase tracking-wider transition-colors ${
                        briefingChannel === ch
                          ? "bg-[#24231f] text-white"
                          : "bg-white border border-[#24231f]/10 text-[#5e5b55]"
                      }`}
                    >
                      {ch}
                    </button>
                  ))}
                </div>
              </div>
              <Link
                href="/funnel-analytics"
                className="inline-flex items-center justify-between px-4 py-2.5 rounded-xl bg-white border border-[#24231f]/15 text-[#24231f] text-xs font-semibold hover:border-[#9673cb] transition-all no-underline"
              >
                <span>Configure Daily Reports</span>
                <span>→</span>
              </Link>
            </article>

            {/* 06: In-DOM Screener Copilot */}
            <article className="p-6 rounded-2xl bg-[#faf7f0]/85 backdrop-blur-xl border border-[#24231f]/12 shadow-sm hover:shadow-md transition-all flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="font-mono text-[10px] text-[#559db3] font-bold uppercase tracking-wider">
                    Chapter 06 / Companion
                  </span>
                  <span className="font-mono text-[9px] px-2 py-0.5 rounded-full bg-[#559db3]/10 text-[#559db3] border border-[#559db3]/20">
                    Manifest V3
                  </span>
                </div>
                <h3 className="font-serif text-xl font-medium text-[#24231f] mb-2 m-0">
                  In-DOM Screener Copilot
                </h3>
                <p className="text-xs text-[#5d5b55] leading-relaxed mb-4">
                  Browser companion that recognizes ATS application forms in real time and crafts grounded answers from candidate compensation and notice period.
                </p>
                <div className="p-3 rounded-xl bg-white/60 backdrop-blur-md border border-[#24231f]/10 mb-4 shadow-xs font-mono text-[10px] space-y-1 text-[#65625c]">
                  <div>🎯 Real-time DOM form detection</div>
                  <div>⚡ 0–90 day notice period model</div>
                  <div>₹ Indian LPA native compensation parser</div>
                </div>
              </div>
              <Link
                href="/student-lab"
                className="inline-flex items-center justify-between px-4 py-2.5 rounded-xl bg-[#24231f] text-white text-xs font-semibold hover:bg-[#3d3b35] transition-all no-underline"
              >
                <span>Launch Screener Lab</span>
                <span>→</span>
              </Link>
            </article>
          </div>
        </section>
      </div>
    </ModuleLayout>
  );
}
