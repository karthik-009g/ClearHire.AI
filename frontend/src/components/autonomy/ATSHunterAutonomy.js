import { useState } from "react";

export default function ATSHunterAutonomy({ onTriggerScan = () => {} }) {
  const [selectedATS, setSelectedATS] = useState("all");
  const [isScanning, setIsScanning] = useState(false);
  const [matchThreshold, setMatchThreshold] = useState(90);

  const partners = [
    {
      company: "Stripe",
      title: "Staff Infrastructure Engineer",
      ats: "Greenhouse",
      location: "San Francisco / Remote",
      match: 99.4,
      comp: "$280k – $340k",
      status: "Direct Requisition",
    },
    {
      company: "Anthropic",
      title: "AI Systems Runtime Architect",
      ats: "Lever",
      location: "San Francisco, CA",
      match: 98.2,
      comp: "$260k – $320k",
      status: "Direct Requisition",
    },
    {
      company: "Figma",
      title: "Distributed Engine Lead",
      ats: "Ashby",
      location: "San Francisco / Remote",
      match: 97.6,
      comp: "$275k – $350k",
      status: "Direct Requisition",
    },
    {
      company: "Datadog",
      title: "Principal Observability Engineer",
      ats: "Workday",
      location: "New York / Remote",
      match: 96.8,
      comp: "$250k – $310k",
      status: "Direct Requisition",
    },
  ];

  const handleRunScan = () => {
    setIsScanning(true);
    onTriggerScan();
    setTimeout(() => {
      setIsScanning(false);
    }, 1200);
  };

  const filtered = selectedATS === "all" ? partners : partners.filter((p) => p.ats.toLowerCase() === selectedATS.toLowerCase());

  return (
    <div className="space-y-4 text-xs font-sans">
      {/* Header telemetry strip */}
      <div className="p-3.5 rounded-xl bg-sky-50/90 border border-sky-200/90 flex items-center justify-between">
        <div>
          <div className="font-mono text-[10px] uppercase tracking-wider text-sky-800 font-bold">
            Autonomy Module 02 // ATS Hunter
          </div>
          <div className="font-serif font-bold text-sm text-sky-950 mt-0.5">
            Direct Corporate Requisition Radar
          </div>
        </div>
        <span className="px-2 py-0.5 rounded-full font-mono text-[10px] font-bold bg-sky-600 text-white shadow-2xs">
          42 ACTIVE PARTNERS
        </span>
      </div>

      {/* ATS Platform Filter */}
      <div className="p-3.5 rounded-xl bg-stone-50 border border-stone-200 space-y-2">
        <div className="flex items-center justify-between font-mono text-[11px] text-stone-700">
          <span>Target Corporate ATS Gateway:</span>
          <span className="text-sky-700 font-bold">{selectedATS.toUpperCase()}</span>
        </div>
        <div className="flex flex-wrap gap-1.5 font-mono text-[10px]">
          {["all", "Greenhouse", "Lever", "Ashby", "Workday"].map((ats) => (
            <button
              key={ats}
              type="button"
              onClick={() => setSelectedATS(ats)}
              className={`px-2.5 py-1 rounded-md border transition-all ${
                selectedATS === ats
                  ? "bg-sky-700 text-white border-sky-800 font-bold shadow-2xs"
                  : "bg-white text-stone-700 border-stone-200 hover:bg-stone-50"
              }`}
            >
              {ats === "all" ? "All Gateways (40+)" : ats}
            </button>
          ))}
        </div>
        <p className="text-[10px] text-stone-500 font-mono mt-1 mb-0">
          0% middleman staffing recruiters. 100% direct corporate ATS webhooks.
        </p>
      </div>

      {/* Match Threshold Filter */}
      <div className="p-3.5 rounded-xl bg-stone-50 border border-stone-200 space-y-2">
        <div className="flex items-center justify-between font-mono text-[11px]">
          <span className="text-stone-600">Minimum Reconciled Match:</span>
          <span className="font-bold text-sky-700">{matchThreshold}% AST Match</span>
        </div>
        <input
          type="range"
          min="80"
          max="98"
          value={matchThreshold}
          onChange={(e) => setMatchThreshold(parseInt(e.target.value, 10))}
          className="w-full accent-sky-700 cursor-pointer"
        />
      </div>

      {/* Live Discovered Requisitions */}
      <div className="space-y-2">
        <div className="flex items-center justify-between font-mono text-[11px] text-stone-600">
          <span>Verified Direct Requisitions:</span>
          <span className="text-sky-700 font-bold">{filtered.length} Matched</span>
        </div>

        <div className="space-y-2 max-h-40 overflow-y-auto pr-1">
          {filtered.map((item) => (
            <div
              key={item.company}
              className="p-2.5 rounded-lg bg-white border border-stone-200/90 shadow-2xs hover:border-sky-300 transition-colors flex items-center justify-between"
            >
              <div className="space-y-0.5">
                <div className="flex items-center gap-2">
                  <strong className="font-serif text-stone-900 text-xs">{item.company}</strong>
                  <span className="px-1.5 py-0.2 rounded bg-stone-100 text-stone-600 font-mono text-[9px]">
                    {item.ats}
                  </span>
                </div>
                <div className="text-[11px] text-stone-600 truncate max-w-[210px]">{item.title}</div>
                <div className="text-[10px] font-mono text-emerald-700">{item.comp}</div>
              </div>

              <div className="text-right">
                <div className="font-mono text-xs font-bold text-sky-700">{item.match}%</div>
                <div className="text-[9px] font-mono text-stone-400">AST Match</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Trigger Live Requisition Scan */}
      <button
        type="button"
        onClick={handleRunScan}
        disabled={isScanning}
        className="w-full py-2.5 px-4 rounded-xl bg-sky-700 hover:bg-sky-800 text-white font-mono font-semibold text-xs shadow-md transition-all flex items-center justify-center gap-2 disabled:opacity-50"
      >
        {isScanning ? (
          <>
            <span className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
            <span>Scanning Direct Corporate ATS Webhooks...</span>
          </>
        ) : (
          <>
            <span>🎯 Scan Partner Requisitions</span>
            <span className="text-[10px] opacity-80">· Real-Time</span>
          </>
        )}
      </button>
    </div>
  );
}
