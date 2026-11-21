import { useState, useEffect } from "react";

export default function SLASentinelAutonomy({
  onTriggerDispatch = () => {},
  onQuickDemo = () => {},
  onSubmitAuth = () => {},
  email = "",
  setEmail = () => {},
  password = "",
  setPassword = () => {},
  busy = false,
  error = "",
}) {
  const [secondsRemaining, setSecondsRemaining] = useState(172752); // ~47h 59m 12s
  const [isDispatching, setIsDispatching] = useState(false);
  const [dispatchLanded, setDispatchLanded] = useState(false);

  useEffect(() => {
    const timer = setInterval(() => {
      setSecondsRemaining((prev) => Math.max(0, prev - 1));
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const formatHours = (secs) => {
    const h = String(Math.floor(secs / 3600)).padStart(2, "0");
    const m = String(Math.floor((secs % 3600) / 60)).padStart(2, "0");
    const s = String(secs % 60).padStart(2, "0");
    return `${h}:${m}:${s}`;
  };

  const handleRunDispatch = () => {
    setIsDispatching(true);
    onTriggerDispatch();
    setTimeout(() => {
      setIsDispatching(false);
      setDispatchLanded(true);
    }, 1500);
  };

  return (
    <div className="space-y-4 text-xs font-sans">
      {/* Header telemetry strip */}
      <div className="p-3.5 rounded-xl bg-amber-50/90 border border-amber-200/90 flex items-center justify-between">
        <div>
          <div className="font-mono text-[10px] uppercase tracking-wider text-amber-800 font-bold">
            Autonomy Module 03 // 48h SLA Sentinel
          </div>
          <div className="font-serif font-bold text-sm text-amber-950 mt-0.5">
            Legally Bound Response Covenant
          </div>
        </div>
        <span className="px-2 py-0.5 rounded-full font-mono text-[10px] font-bold bg-amber-600 text-white shadow-2xs">
          ENFORCEABLE SLA
        </span>
      </div>

      {/* 48-Hour SLA Chronometer */}
      <div className="p-4 rounded-xl bg-stone-900 text-white space-y-2 text-center shadow-inner">
        <div className="font-mono text-[10px] uppercase tracking-widest text-emerald-400">
          ● GUARANTEED HIRING MANAGER RESPONSE WINDOW
        </div>
        <div className="font-mono text-3xl font-bold tracking-wider text-white">
          {formatHours(secondsRemaining)}
        </div>
        <div className="text-[10px] font-mono text-stone-400 flex items-center justify-center gap-3">
          <span>Stripe · Anthropic · Figma</span>
          <span>·</span>
          <span className="text-emerald-400 font-semibold">100% Feedback SLA</span>
        </div>
      </div>

      {/* Dispatch Action */}
      <div className="p-3.5 rounded-xl bg-stone-50 border border-stone-200 space-y-2.5">
        <div className="flex items-center justify-between font-mono text-[11px] text-stone-700">
          <span>Pneumatic Conduit Dispatch:</span>
          <span className={dispatchLanded ? "text-emerald-700 font-bold" : "text-amber-700 font-bold"}>
            {dispatchLanded ? "LANDED ON EXEC DESK ✓" : "READY FOR LAUNCH"}
          </span>
        </div>

        <button
          type="button"
          onClick={handleRunDispatch}
          disabled={isDispatching}
          className="w-full py-2 px-3 rounded-lg bg-stone-800 hover:bg-stone-900 text-white font-mono text-xs font-semibold shadow-xs transition-all flex items-center justify-center gap-2 disabled:opacity-50"
        >
          {isDispatching ? (
            <>
              <span className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
              <span>Accelerating Through Pneumatic Conduit...</span>
            </>
          ) : (
            <>
              <span>🚀 Fire Pneumatic Tube Dispatch</span>
              <span className="text-[10px] text-stone-400">· 48 km/h</span>
            </>
          )}
        </button>
      </div>

      {/* Candidate Enclave Authentication Form */}
      <div className="p-3.5 rounded-xl bg-white border border-stone-200 shadow-sm space-y-3">
        <div className="flex items-center justify-between">
          <span className="font-mono text-[11px] uppercase tracking-wider text-emerald-800 font-bold">
            Sign In to Candidate Workspace
          </span>
          <button
            type="button"
            onClick={onQuickDemo}
            className="text-[10px] font-mono text-emerald-700 hover:text-emerald-900 underline font-semibold"
          >
            ⚡ Sarah Chen Demo
          </button>
        </div>

        {error && (
          <div className="p-2.5 rounded-lg bg-red-50 border border-red-200 text-red-800 text-[11px] font-mono leading-tight">
            {typeof error === "string" ? error : (error?.message || JSON.stringify(error))}
          </div>
        )}

        <form onSubmit={onSubmitAuth} className="space-y-2">
          <div>
            <label className="block text-[10px] font-mono text-stone-500 mb-0.5">Candidate Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="sarah.chen@alum.mit.edu"
              className="w-full px-2.5 py-1.5 rounded-md border border-stone-300 text-stone-900 bg-stone-50/50 font-mono text-xs focus:outline-none focus:ring-1 focus:ring-emerald-600"
            />
          </div>

          <div>
            <label className="block text-[10px] font-mono text-stone-500 mb-0.5">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••••••"
              className="w-full px-2.5 py-1.5 rounded-md border border-stone-300 text-stone-900 bg-stone-50/50 font-mono text-xs focus:outline-none focus:ring-1 focus:ring-emerald-600"
            />
          </div>

          <button
            type="submit"
            disabled={busy}
            className="w-full py-2 px-3 rounded-lg bg-emerald-700 hover:bg-emerald-800 text-white font-mono font-semibold text-xs shadow-xs transition-all disabled:opacity-50 mt-1"
          >
            {busy ? "Authenticating..." : "Enter Candidate Workspace →"}
          </button>
        </form>
      </div>
    </div>
  );
}
