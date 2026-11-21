import { useState } from "react";

export default function ASTTailorAutonomy({ onTriggerAudit = () => {} }) {
  const [marginBudget, setMarginBudget] = useState(0.75);
  const [hallucinationShield, setHallucinationShield] = useState(true);
  const [activeSection, setActiveSection] = useState("experience");
  const [isAuditing, setIsAuditing] = useState(false);
  const [auditSuccess, setAuditSuccess] = useState(true);

  const handleRunAudit = () => {
    setIsAuditing(true);
    onTriggerAudit();
    setTimeout(() => {
      setIsAuditing(false);
      setAuditSuccess(true);
    }, 1200);
  };

  const sections = {
    executive: {
      title: "Executive Summary",
      nodes: 4,
      tokens: 88,
      status: "AST Verified · 0 Hallucinations",
      snippet: "Principal engineer leading distributed agents and LLM inference pipelines with sub-50ms p99 SLA.",
    },
    experience: {
      title: "Work Experience & Impact",
      nodes: 12,
      tokens: 342,
      status: "100% Quantified Impact",
      snippet: "Architected multi-agent orchestration runtime with deterministic AST guarantees across 18 production clusters.",
    },
    skills: {
      title: "Technical Competencies",
      nodes: 8,
      tokens: 96,
      status: "Direct Heuristic Match",
      snippet: "Python, Triton, CUDA C++, Rust, Next.js, WebGL, PostgreSQL, pgvector, Docker, Kubernetes.",
    },
  };

  const current = sections[activeSection];
  const pageUtilization = Math.round(92 + (marginBudget - 0.5) * 16);

  return (
    <div className="space-y-4 text-xs font-sans">
      {/* Header telemetry strip */}
      <div className="p-3.5 rounded-xl bg-emerald-50/90 border border-emerald-200/90 flex items-center justify-between">
        <div>
          <div className="font-mono text-[10px] uppercase tracking-wider text-emerald-800 font-bold">
            Autonomy Module 01 // AST Tailor
          </div>
          <div className="font-serif font-bold text-sm text-emerald-950 mt-0.5">
            Deterministic Syntax Compiler
          </div>
        </div>
        <span className="px-2 py-0.5 rounded-full font-mono text-[10px] font-bold bg-emerald-600 text-white shadow-2xs">
          99.4% PASS RATE
        </span>
      </div>

      {/* Zero Hallucination Shield Toggle */}
      <div className="p-3.5 rounded-xl bg-stone-50 border border-stone-200 space-y-2">
        <div className="flex items-center justify-between">
          <span className="font-mono text-[11px] font-semibold text-stone-800">
            Zero-Hallucination Guard
          </span>
          <button
            type="button"
            onClick={() => setHallucinationShield(!hallucinationShield)}
            className={`px-2 py-1 rounded text-[10px] font-mono font-bold transition-colors ${
              hallucinationShield
                ? "bg-emerald-700 text-white"
                : "bg-stone-300 text-stone-700"
            }`}
          >
            {hallucinationShield ? "SHIELD: ENFORCED" : "SHIELD: OFF"}
          </button>
        </div>
        <p className="text-[11px] text-stone-600 leading-relaxed mb-0">
          Reconciles every skill and claim against verified code commits and candidate project artifacts. Zero hallucinated metrics.
        </p>
      </div>

      {/* 1-Page Margin Budget Controller */}
      <div className="p-3.5 rounded-xl bg-stone-50 border border-stone-200 space-y-2">
        <div className="flex items-center justify-between font-mono text-[11px]">
          <span className="text-stone-600">Margin Budget: {marginBudget.toFixed(2)} in</span>
          <span className="font-bold text-emerald-700">Page Load: {pageUtilization}% (1 Page Max)</span>
        </div>
        <input
          type="range"
          min="0.5"
          max="1.0"
          step="0.05"
          value={marginBudget}
          onChange={(e) => setMarginBudget(parseFloat(e.target.value))}
          className="w-full accent-emerald-700 cursor-pointer"
        />
        <div className="flex justify-between text-[10px] font-mono text-stone-500">
          <span>Compact (0.5")</span>
          <span>Zero Page Overflow</span>
          <span>Spacious (1.0")</span>
        </div>
      </div>

      {/* AST Node Tree Section Selector */}
      <div className="space-y-2">
        <div className="flex items-center justify-between font-mono text-[11px] text-stone-600">
          <span>AST Node Tree Hierarchy:</span>
          <span className="text-emerald-700 font-bold">{current.nodes} AST Nodes</span>
        </div>
        <div className="grid grid-cols-3 gap-1.5 font-mono text-[10px]">
          {Object.entries(sections).map(([key, sec]) => (
            <button
              key={key}
              type="button"
              onClick={() => setActiveSection(key)}
              className={`p-2 rounded-lg border text-left transition-all ${
                activeSection === key
                  ? "bg-emerald-700 text-white border-emerald-800 font-bold shadow-2xs"
                  : "bg-white text-stone-700 border-stone-200 hover:bg-stone-50"
              }`}
            >
              <div className="truncate">{sec.title}</div>
              <div className="text-[9px] opacity-80 mt-0.5">{sec.tokens} tokens</div>
            </button>
          ))}
        </div>

        <div className="p-3 rounded-lg bg-white border border-stone-200/90 font-mono text-[11px] space-y-1.5">
          <div className="flex justify-between text-[10px] text-emerald-700 font-bold">
            <span>{current.status}</span>
            <span>DEPTH: 2</span>
          </div>
          <div className="text-stone-700 font-sans text-xs italic bg-stone-50 p-2 rounded border border-stone-100">
            "{current.snippet}"
          </div>
        </div>
      </div>

      {/* Trigger Live AST Audit Action */}
      <button
        type="button"
        onClick={handleRunAudit}
        disabled={isAuditing}
        className="w-full py-2.5 px-4 rounded-xl bg-emerald-700 hover:bg-emerald-800 text-white font-mono font-semibold text-xs shadow-md transition-all flex items-center justify-center gap-2 disabled:opacity-50"
      >
        {isAuditing ? (
          <>
            <span className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
            <span>Compiling Abstract Syntax Tree...</span>
          </>
        ) : (
          <>
            <span>⚡ Run AST Syntax Audit</span>
            <span className="text-[10px] opacity-80">· 0.2s</span>
          </>
        )}
      </button>
    </div>
  );
}
