import { useEffect, useRef, useState, useCallback } from "react";
import Link from "next/link";
import { useRouter } from "next/router";
import dynamic from "next/dynamic";
import { getMe, loginUser, registerUser } from "../api/auth";
import { clearAuthToken, getStoredAuthToken, setAuthToken } from "../api/client";
import { VirtualScroll } from "../lib/VirtualScroll";
import { STORY_STAGES } from "../components/ClearHireStoryEngine";

// Dynamically import ClearHireStoryEngine with SSR disabled
const ClearHireStoryEngine = dynamic(() => import("../components/ClearHireStoryEngine"), {
  ssr: false,
  loading: () => (
    <div className="fixed inset-0 w-full h-full bg-[#f6f4ee] flex flex-col items-center justify-center gap-3 text-[#24231f]">
      <div className="w-10 h-10 rounded-full border-2 border-[#15803d] border-t-transparent animate-spin" />
      <span className="font-mono text-xs uppercase tracking-widest text-[#706e68]">
        Initializing ClearHire 3D Office World & Story Engine...
      </span>
    </div>
  ),
});

export default function LoginPage() {
  const router = useRouter();

  // Active Story Stage (0 to 8)
  const [activeStage, setActiveStage] = useState(0);
  const [activeBranch, setActiveBranch] = useState("clearhire"); // "legacy" vs "clearhire"
  const activeStageRef = useRef(activeStage);
  useEffect(() => {
    activeStageRef.current = activeStage;
  }, [activeStage]);

  // Spatial Telemetry Anchors & Dynamic SVG Dogleg Leader Lines (Phase 5)
  const platenTagRef = useRef(null);
  const pneumaticTagRef = useRef(null);
  const chronoTagRef = useRef(null);
  const resumeTagRef = useRef(null);

  const resumePathRef = useRef(null);
  const resumeReticleDotRef = useRef(null);
  const resumeReticleRingRef = useRef(null);

  const platenPathRef = useRef(null);
  const platenReticleDotRef = useRef(null);
  const platenReticleRingRef = useRef(null);

  const pneumaticPathRef = useRef(null);
  const pneumaticReticleDotRef = useRef(null);
  const pneumaticReticleRingRef = useRef(null);

  const chronoPathRef = useRef(null);
  const chronoReticleDotRef = useRef(null);
  const chronoReticleRingRef = useRef(null);

  const handleSpatialTelemetry = useCallback((anchors) => {
    if (!anchors) return;
    const stage = activeStageRef.current;

    // 1. Candidate Resume Telemetry Tag (Active on stages 0 and 1)
    const pr = anchors.resume;
    if (pr && pr.visible && (stage === 0 || stage === 1)) {
      const ex = pr.x + 36;
      const ey = pr.y - 24;
      const cx = pr.x + 85;
      const cy = pr.y - 24;
      if (resumePathRef.current) {
        resumePathRef.current.setAttribute("d", `M ${pr.x.toFixed(1)} ${pr.y.toFixed(1)} L ${ex.toFixed(1)} ${ey.toFixed(1)} L ${cx.toFixed(1)} ${cy.toFixed(1)}`);
        resumePathRef.current.style.opacity = "1";
      }
      if (resumeReticleDotRef.current) {
        resumeReticleDotRef.current.setAttribute("cx", pr.x.toFixed(1));
        resumeReticleDotRef.current.setAttribute("cy", pr.y.toFixed(1));
        resumeReticleDotRef.current.style.opacity = "1";
      }
      if (resumeReticleRingRef.current) {
        resumeReticleRingRef.current.setAttribute("cx", pr.x.toFixed(1));
        resumeReticleRingRef.current.setAttribute("cy", pr.y.toFixed(1));
        resumeReticleRingRef.current.style.opacity = "1";
      }
      if (resumeTagRef.current) {
        resumeTagRef.current.style.transform = `translate3d(${cx + 8}px, ${cy - 18}px, 0)`;
        resumeTagRef.current.style.opacity = "1";
      }
    } else {
      if (resumePathRef.current) resumePathRef.current.style.opacity = "0";
      if (resumeReticleDotRef.current) resumeReticleDotRef.current.style.opacity = "0";
      if (resumeReticleRingRef.current) resumeReticleRingRef.current.style.opacity = "0";
      if (resumeTagRef.current) resumeTagRef.current.style.opacity = "0";
    }

    // 2. Square Robot ATS Platen Tag (Active on stages 2 and 3)
    const pp = anchors.platen;
    if (pp && pp.visible && (stage === 2 || stage === 3)) {
      const ex = pp.x + 32;
      const ey = pp.y - 30;
      const cx = pp.x + 85;
      const cy = pp.y - 30;
      if (platenPathRef.current) {
        platenPathRef.current.setAttribute("d", `M ${pp.x.toFixed(1)} ${pp.y.toFixed(1)} L ${ex.toFixed(1)} ${ey.toFixed(1)} L ${cx.toFixed(1)} ${cy.toFixed(1)}`);
        platenPathRef.current.style.opacity = "1";
      }
      if (platenReticleDotRef.current) {
        platenReticleDotRef.current.setAttribute("cx", pp.x.toFixed(1));
        platenReticleDotRef.current.setAttribute("cy", pp.y.toFixed(1));
        platenReticleDotRef.current.style.opacity = "1";
      }
      if (platenReticleRingRef.current) {
        platenReticleRingRef.current.setAttribute("cx", pp.x.toFixed(1));
        platenReticleRingRef.current.setAttribute("cy", pp.y.toFixed(1));
        platenReticleRingRef.current.style.opacity = "1";
      }
      if (platenTagRef.current) {
        platenTagRef.current.style.transform = `translate3d(${cx + 8}px, ${cy - 18}px, 0)`;
        platenTagRef.current.style.opacity = "1";
      }
    } else {
      if (platenPathRef.current) platenPathRef.current.style.opacity = "0";
      if (platenReticleDotRef.current) platenReticleDotRef.current.style.opacity = "0";
      if (platenReticleRingRef.current) platenReticleRingRef.current.style.opacity = "0";
      if (platenTagRef.current) platenTagRef.current.style.opacity = "0";
    }

    // 3. Pneumatic Velocity Rail Tag (Active on stages 6 and 7)
    const pn = anchors.pneumatic;
    if (pn && pn.visible && (stage === 6 || stage === 7)) {
      const ex = pn.x + 36;
      const ey = pn.y - 22;
      const cx = pn.x + 85;
      const cy = pn.y - 22;
      if (pneumaticPathRef.current) {
        pneumaticPathRef.current.setAttribute("d", `M ${pn.x.toFixed(1)} ${pn.y.toFixed(1)} L ${ex.toFixed(1)} ${ey.toFixed(1)} L ${cx.toFixed(1)} ${cy.toFixed(1)}`);
        pneumaticPathRef.current.style.opacity = "1";
      }
      if (pneumaticReticleDotRef.current) {
        pneumaticReticleDotRef.current.setAttribute("cx", pn.x.toFixed(1));
        pneumaticReticleDotRef.current.setAttribute("cy", pn.y.toFixed(1));
        pneumaticReticleDotRef.current.style.opacity = "1";
      }
      if (pneumaticReticleRingRef.current) {
        pneumaticReticleRingRef.current.setAttribute("cx", pn.x.toFixed(1));
        pneumaticReticleRingRef.current.setAttribute("cy", pn.y.toFixed(1));
        pneumaticReticleRingRef.current.style.opacity = "1";
      }
      if (pneumaticTagRef.current) {
        pneumaticTagRef.current.style.transform = `translate3d(${cx + 8}px, ${cy - 18}px, 0)`;
        pneumaticTagRef.current.style.opacity = "1";
      }
    } else {
      if (pneumaticPathRef.current) pneumaticPathRef.current.style.opacity = "0";
      if (pneumaticReticleDotRef.current) pneumaticReticleDotRef.current.style.opacity = "0";
      if (pneumaticReticleRingRef.current) pneumaticReticleRingRef.current.style.opacity = "0";
      if (pneumaticTagRef.current) pneumaticTagRef.current.style.opacity = "0";
    }

    // 4. Executive Chronometer SLA Tag (Active on stages 7 and 8)
    const pc = anchors.chrono;
    if (pc && pc.visible && (stage === 7 || stage === 8)) {
      const ex = pc.x - 36;
      const ey = pc.y - 24;
      const cx = pc.x - 85;
      const cy = pc.y - 24;
      if (chronoPathRef.current) {
        chronoPathRef.current.setAttribute("d", `M ${pc.x.toFixed(1)} ${pc.y.toFixed(1)} L ${ex.toFixed(1)} ${ey.toFixed(1)} L ${cx.toFixed(1)} ${cy.toFixed(1)}`);
        chronoPathRef.current.style.opacity = "1";
      }
      if (chronoReticleDotRef.current) {
        chronoReticleDotRef.current.setAttribute("cx", pc.x.toFixed(1));
        chronoReticleDotRef.current.setAttribute("cy", pc.y.toFixed(1));
        chronoReticleDotRef.current.style.opacity = "1";
      }
      if (chronoReticleRingRef.current) {
        chronoReticleRingRef.current.setAttribute("cx", pc.x.toFixed(1));
        chronoReticleRingRef.current.setAttribute("cy", pc.y.toFixed(1));
        chronoReticleRingRef.current.style.opacity = "1";
      }
      if (chronoTagRef.current) {
        chronoTagRef.current.style.transform = `translate3d(${cx - 240}px, ${cy - 18}px, 0)`;
        chronoTagRef.current.style.opacity = "1";
      }
    } else {
      if (chronoPathRef.current) chronoPathRef.current.style.opacity = "0";
      if (chronoReticleDotRef.current) chronoReticleDotRef.current.style.opacity = "0";
      if (chronoReticleRingRef.current) chronoReticleRingRef.current.style.opacity = "0";
      if (chronoTagRef.current) chronoTagRef.current.style.opacity = "0";
    }
  }, []);

  // Continuous motion tracking
  const virtualScrollRef = useRef(null);
  const motionRef = useRef({ progress: 0, velocity: 0, speed: 0, continuousChapter: 0 });
  const scrubberRef = useRef(null);

  // Telemetry state
  const [telemetryVelocity, setTelemetryVelocity] = useState("0.00 c");

  // Auth Form State
  const [authMode, setAuthMode] = useState("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  // Toast Notification State
  const [toastMessage, setToastMessage] = useState("");
  const toastTimeoutRef = useRef(null);

  const showToast = useCallback((msg) => {
    if (toastTimeoutRef.current) clearTimeout(toastTimeoutRef.current);
    setToastMessage(msg);
    toastTimeoutRef.current = setTimeout(() => setToastMessage(""), 3500);
  }, []);

  // Check existing active session
  useEffect(() => {
    let active = true;
    const checkSession = async () => {
      const token = getStoredAuthToken();
      if (!token) return;
      try {
        setAuthToken(token);
        await getMe();
        if (active) router.replace("/");
      } catch {
        clearAuthToken();
      }
    };
    checkSession();
    return () => {
      active = false;
    };
  }, [router]);

  // Extended Virtual Momentum Scroll (9 stages: 0.0 to 8.0)
  useEffect(() => {
    const vs = new VirtualScroll({ maxProgress: 8.0, sensitivity: 0.0016 });
    virtualScrollRef.current = vs;
    vs.bindEvents();

    vs.onUpdate((current, velocity, speed) => {
      const normalized = Math.max(0, Math.min(1, current / 8.0));
      motionRef.current.progress = normalized;
      motionRef.current.velocity = velocity;
      motionRef.current.speed = speed;
      motionRef.current.continuousChapter = current;

      if (scrubberRef.current) {
        scrubberRef.current.style.transform = `scaleX(${normalized})`;
      }
      setTelemetryVelocity(`${(Math.abs(velocity) * 1.8).toFixed(2)} c`);
    });

    vs.onSectorChange((sector) => {
      setActiveStage(sector);
    });

    let animId;
    let lastTime = performance.now();
    const updateLoop = () => {
      const now = performance.now();
      const dt = Math.min(0.1, (now - lastTime) / 1000);
      lastTime = now;
      vs.update(dt || 0.016);
      animId = requestAnimationFrame(updateLoop);
    };
    animId = requestAnimationFrame(updateLoop);

    return () => {
      cancelAnimationFrame(animId);
      vs.unbindEvents();
    };
  }, []);

  // Stage Navigation Helpers
  const scrollToStage = useCallback((index) => {
    virtualScrollRef.current?.scrollToSector(index);
  }, []);

  const nextStage = useCallback(() => {
    virtualScrollRef.current?.nextSector();
  }, []);

  const prevStage = useCallback(() => {
    virtualScrollRef.current?.prevSector();
  }, []);

  useEffect(() => {
    if (typeof window !== "undefined") {
      window.__clearhire_scrollToStage = scrollToStage;
    }
  }, [scrollToStage]);

  // Keyboard Navigation
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") return;
      if (e.key === "ArrowDown" || e.key === "ArrowRight" || e.key === "PageDown") {
        e.preventDefault();
        nextStage();
      } else if (e.key === "ArrowUp" || e.key === "ArrowLeft" || e.key === "PageUp") {
        e.preventDefault();
        prevStage();
      } else if (e.key >= "1" && e.key <= "9") {
        const targetIdx = parseInt(e.key, 10) - 1;
        scrollToStage(targetIdx);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [nextStage, prevStage, scrollToStage]);

  // Instant 1-Click Demo Login
  const handleInstantDemoLogin = async () => {
    const demoEmail = "candidate.demo@clearhire.ai";
    const demoPassword = "Password123!";
    setEmail(demoEmail);
    setPassword(demoPassword);
    setConfirmPassword(demoPassword);
    setError("");
    setBusy(true);
    showToast("Authenticating Sarah Chen credentials...");
    try {
      let tokenPayload;
      try {
        tokenPayload = await loginUser(demoEmail, demoPassword);
      } catch {
        try {
          await registerUser(demoEmail, demoPassword);
          tokenPayload = await loginUser(demoEmail, demoPassword);
        } catch (rErr) {
          throw rErr;
        }
      }
      setAuthToken(tokenPayload.access_token);
      await getMe();
      showToast("Access verified. Entering ClearHire workspace...");
      router.push("/");
    } catch (err) {
      setError(err.message || "Demo login failed.");
    } finally {
      setBusy(false);
    }
  };

  // Auth Form Submit
  const onSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setBusy(true);

    if (authMode === "signup" && password !== confirmPassword) {
      setError("Passwords do not match.");
      setBusy(false);
      return;
    }

    try {
      let tokenPayload;
      if (authMode === "signin") {
        tokenPayload = await loginUser(email, password);
      } else {
        await registerUser(email, password);
        tokenPayload = await loginUser(email, password);
      }
      setAuthToken(tokenPayload.access_token);
      await getMe();
      showToast("Access verified. Entering workspace...");
      router.push("/");
    } catch (err) {
      setError(err.message || "Authentication failed. Check your credentials.");
    } finally {
      setBusy(false);
    }
  };

  const currentStageData = STORY_STAGES[activeStage] || STORY_STAGES[0];

  return (
    <div id="clearhire-story-world" className="relative w-screen h-screen overflow-hidden bg-[#f6f4ee] text-[#24231f] font-sans select-none">
      {/* 1. Global Reading Progress Track */}
      <div className="fixed top-0 left-0 right-0 h-[3px] z-50 pointer-events-none">
        <div
          ref={scrubberRef}
          className="h-full origin-left bg-gradient-to-r from-[#15803d] via-[#38bdf8] to-[#d4af37]"
          style={{ transform: "scaleX(0)" }}
        />
      </div>

      {/* 2. Top Architectural Header */}
      <header className="fixed top-5 left-6 right-6 z-40 flex items-center justify-between pointer-events-none">
        {/* Brand */}
        <div className="pointer-events-auto flex items-center gap-3 bg-[#faf7f0]/90 backdrop-blur-xl px-4 py-2 rounded-full border border-[#24231f]/12 shadow-md">
          <span className="w-2.5 h-2.5 rounded-full bg-[#15803d] shadow-[0_0_10px_rgba(21,128,61,0.5)] animate-pulse" />
          <button
            type="button"
            onClick={() => scrollToStage(0)}
            className="flex items-baseline gap-0.5 text-sm font-bold tracking-tight text-[#24231f] hover:text-[#15803d] transition-colors"
          >
            <span className="font-serif text-base font-bold">clearhire</span>
            <span className="text-[#15803d] font-mono text-xs">.ai</span>
          </button>
          <span className="text-[#706e68]/40 text-xs">/</span>
          <span className="font-mono text-[10px] tracking-wider text-[#706e68] uppercase font-semibold">
            3D SPATIAL AUTONOMY ENGINE
          </span>
        </div>

        {/* Center: Branch Switcher & Telemetry */}
        <div className="hidden lg:flex pointer-events-auto items-center gap-4 bg-[#faf7f0]/90 backdrop-blur-xl px-4 py-1.5 rounded-full border border-[#24231f]/12 shadow-md">
          {/* Branch Toggle */}
          <div className="flex items-center gap-1 p-0.5 bg-[#eeece2] rounded-full">
            <button
              type="button"
              onClick={() => {
                setActiveBranch("clearhire");
                showToast("ClearHire Covenant Route Active (48h SLA)");
              }}
              className={`font-mono text-[11px] px-3 py-1 rounded-full font-bold transition-all ${
                activeBranch === "clearhire"
                  ? "bg-[#15803d] text-white shadow-xs"
                  : "text-[#706e68] hover:text-[#24231f]"
              }`}
            >
              ✨ CLEARHIRE 48H SLA
            </button>
            <button
              type="button"
              onClick={() => {
                setActiveBranch("legacy");
                showToast("Legacy ATS Trap Route Active (Heuristic Rejection)");
              }}
              className={`font-mono text-[11px] px-3 py-1 rounded-full font-bold transition-all ${
                activeBranch === "legacy"
                  ? "bg-[#b91c1c] text-white shadow-xs"
                  : "text-[#706e68] hover:text-[#24231f]"
              }`}
            >
              ⚠️ LEGACY TRAP
            </button>
          </div>

          <span className="w-px h-5 bg-[#24231f]/10" />

          {/* Telemetry Indicator */}
          <div className="flex items-center gap-2 font-mono text-[11px]">
            <span className="text-[#706e68] uppercase">STAGE</span>
            <span className="text-[#15803d] font-bold">
              {currentStageData.num} // {currentStageData.badge}
            </span>
          </div>
        </div>

        {/* Right: Quick Action to Stage 09 Portal */}
        <div className="pointer-events-auto flex items-center gap-3">
          <button
            type="button"
            onClick={() => scrollToStage(8)}
            className="flex items-center gap-2 bg-[#24231f] hover:bg-[#3d3a33] text-white px-5 py-2 rounded-full text-xs font-mono font-bold transition-all shadow-md active:scale-95"
          >
            <span className="w-1.5 h-1.5 rounded-full bg-[#34d399] animate-pulse" />
            <span>SKIP TO LOGIN (STAGE 09)</span>
            <span>→</span>
          </button>
        </div>
      </header>

      {/* 3. 3D Spatial Story Engine Canvas (Grounding the Office World) */}
      <ClearHireStoryEngine
        motionRef={motionRef}
        activeBranch={activeBranch}
        onStageChange={(stage) => setActiveStage(stage)}
        onSpatialTelemetry={handleSpatialTelemetry}
      />

      {/* Dynamic Architectural SVG Leader Lines & Reticles Overlay (Phase 5) */}
      <svg className="fixed inset-0 pointer-events-none z-20 w-full h-full overflow-hidden" aria-hidden="true">
        {/* Resume Leader & Reticle */}
        <path ref={resumePathRef} fill="none" stroke="#15803d" strokeWidth="1.2" strokeDasharray="4 3" opacity="0" className="transition-opacity duration-300" />
        <circle ref={resumeReticleDotRef} r="3" fill="#15803d" opacity="0" className="transition-opacity duration-300" />
        <circle ref={resumeReticleRingRef} r="9" fill="none" stroke="#15803d" strokeWidth="1" strokeDasharray="3 2" opacity="0" className="transition-opacity duration-300 animate-pulse" />

        {/* Platen Leader & Reticle */}
        <path ref={platenPathRef} fill="none" stroke="#0284c7" strokeWidth="1.2" strokeDasharray="4 3" opacity="0" className="transition-opacity duration-300" />
        <circle ref={platenReticleDotRef} r="3" fill="#0284c7" opacity="0" className="transition-opacity duration-300" />
        <circle ref={platenReticleRingRef} r="9" fill="none" stroke="#0284c7" strokeWidth="1" strokeDasharray="3 2" opacity="0" className="transition-opacity duration-300 animate-pulse" />

        {/* Pneumatic Leader & Reticle */}
        <path ref={pneumaticPathRef} fill="none" stroke="#10b981" strokeWidth="1.2" strokeDasharray="4 3" opacity="0" className="transition-opacity duration-300" />
        <circle ref={pneumaticReticleDotRef} r="3" fill="#10b981" opacity="0" className="transition-opacity duration-300" />
        <circle ref={pneumaticReticleRingRef} r="9" fill="none" stroke="#10b981" strokeWidth="1" strokeDasharray="3 2" opacity="0" className="transition-opacity duration-300 animate-pulse" />

        {/* Chrono Leader & Reticle */}
        <path ref={chronoPathRef} fill="none" stroke="#d97706" strokeWidth="1.2" strokeDasharray="4 3" opacity="0" className="transition-opacity duration-300" />
        <circle ref={chronoReticleDotRef} r="3" fill="#d97706" opacity="0" className="transition-opacity duration-300" />
        <circle ref={chronoReticleRingRef} r="9" fill="none" stroke="#d97706" strokeWidth="1" strokeDasharray="3 2" opacity="0" className="transition-opacity duration-300 animate-pulse" />
      </svg>

      {/* Spatial 3D UI Telemetry Anchors (Phase 5: High-Density Micro-Telemetry Chips) */}
      <div className="fixed inset-0 pointer-events-none z-20 overflow-hidden" aria-hidden="true">
        {/* Candidate Resume Anchor */}
        <div
          ref={resumeTagRef}
          className="absolute left-0 top-0 transition-opacity duration-300 opacity-0 will-change-transform"
        >
          <div className="px-3 py-1.5 rounded-xl bg-[#faf7f0]/95 backdrop-blur-md border border-[#15803d]/25 shadow-lg font-mono text-[9px] text-[#24231f] flex flex-col gap-0.5">
            <div className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-[#15803d] animate-ping" />
              <span className="text-[#15803d] font-bold tracking-wider">DOSSIER</span>
              <span className="text-[#24231f]/60">// SARAH CHEN (MIT)</span>
            </div>
            <div className="text-[8px] text-[#24231f]/60 flex items-center gap-2">
              <span>CONF: 99.4%</span>
              <span className="text-[#15803d]">LAT: 42ms</span>
              <span>SEC: ED25519</span>
            </div>
          </div>
        </div>

        {/* Platen Intake Anchor */}
        <div
          ref={platenTagRef}
          className="absolute left-0 top-0 transition-opacity duration-300 opacity-0 will-change-transform"
        >
          <div className="px-3 py-1.5 rounded-xl bg-[#faf7f0]/95 backdrop-blur-md border border-[#0284c7]/25 shadow-lg font-mono text-[9px] text-[#24231f] flex flex-col gap-0.5">
            <div className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-[#0284c7] animate-ping" />
              <span className="text-[#0284c7] font-bold tracking-wider">OPTICAL PLATEN</span>
              <span className="text-[#24231f]/60">// 1200 DPI OCR</span>
            </div>
            <div className="text-[8px] text-[#24231f]/60 flex items-center gap-2">
              <span>LAMBDA: 488nm</span>
              <span className="text-[#0284c7]">AST: PARSING</span>
              <span>PASS: 99.8%</span>
            </div>
          </div>
        </div>

        {/* Pneumatic Conduit Anchor */}
        <div
          ref={pneumaticTagRef}
          className="absolute left-0 top-0 transition-opacity duration-300 opacity-0 will-change-transform"
        >
          <div className="px-3 py-1.5 rounded-xl bg-[#faf7f0]/95 backdrop-blur-md border border-[#10b981]/25 shadow-lg font-mono text-[9px] text-[#24231f] flex flex-col gap-0.5">
            <div className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-[#10b981] animate-ping" />
              <span className="text-[#059669] font-bold tracking-wider">PNEUMATIC RAIL</span>
              <span className="text-[#24231f]/60">// BRASS CONDUIT</span>
            </div>
            <div className="text-[8px] text-[#24231f]/60 flex items-center gap-2">
              <span>VELOCITY: 48 KM/H</span>
              <span className="text-[#059669]">BYPASS: 100%</span>
              <span>LOSS: 0.00%</span>
            </div>
          </div>
        </div>

        {/* Executive SLA Chronometer Anchor */}
        <div
          ref={chronoTagRef}
          className="absolute left-0 top-0 transition-opacity duration-300 opacity-0 will-change-transform"
        >
          <div className="px-3 py-1.5 rounded-xl bg-[#faf7f0]/95 backdrop-blur-md border border-[#d97706]/25 shadow-lg font-mono text-[9px] text-[#24231f] flex flex-col gap-0.5">
            <div className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-[#d97706] animate-ping" />
              <span className="text-[#b45309] font-bold tracking-wider">48H SLA COVENANT</span>
              <span className="text-[#24231f]/60">// EXEC ENCLAVE</span>
            </div>
            <div className="text-[8px] text-[#24231f]/60 flex items-center gap-2">
              <span>SLA: ACTIVE</span>
              <span className="text-[#b45309]">T-MINUS 47:58:22</span>
              <span>DIRECT HIRE</span>
            </div>
          </div>
        </div>
      </div>

      {/* 4. Floating Editorial Story Narrative Card (Left-Aligned, Non-Obtrusive) */}
      {activeStage < 8 && (
        <aside
          aria-label="Story narrative"
          className="fixed left-8 top-28 z-30 max-w-sm pointer-events-auto transition-all duration-500 ease-out animate-fadeIn"
        >
          <div className="rounded-2xl p-6 bg-[#faf7f0]/85 border border-[#24231f]/12 shadow-xl backdrop-blur-xl flex flex-col gap-3">
            {/* Stage Badge & Coordinates */}
            <div className="flex items-center justify-between gap-2 border-b border-[#24231f]/10 pb-2.5">
              <span
                className={`font-mono text-[10px] uppercase font-bold tracking-wider px-2.5 py-0.5 rounded-full border ${
                  activeBranch === "legacy" && activeStage >= 3 && activeStage <= 5
                    ? "bg-red-500/10 text-red-700 border-red-500/30"
                    : "bg-[#15803d]/10 text-[#15803d] border-[#15803d]/30"
                }`}
              >
                {currentStageData.badge}
              </span>
              <span className="font-mono text-[10px] text-[#706e68]">
                {currentStageData.coordinates}
              </span>
            </div>

            {/* Title & Narrative */}
            <div>
              <span className="font-mono text-[11px] text-[#706e68] uppercase font-semibold">
                STAGE {currentStageData.num} OF 09
              </span>
              <h2 className="font-serif text-2xl font-bold text-[#24231f] tracking-tight mt-0.5">
                {currentStageData.title}
              </h2>
              <p className="font-sans text-xs text-[#525048] leading-relaxed mt-2">
                {currentStageData.narrative}
              </p>
            </div>

            {/* Technical Telemetry Strip (Anatomy Skill Style) */}
            <div className="p-2.5 rounded-xl bg-white/70 border border-[#24231f]/8 font-mono text-[10px] space-y-1 text-[#24231f]">
              <div className="flex items-center justify-between">
                <span className="text-[#706e68] uppercase">Scanner Status:</span>
                <span className="font-bold text-[#15803d]">{currentStageData.scannerStatus}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-[#706e68] uppercase">Target Node:</span>
                <span className="font-semibold">{currentStageData.destination}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-[#706e68] uppercase">Robot Mood:</span>
                <span className="uppercase font-bold text-[#5369d9]">{currentStageData.robotMood}</span>
              </div>
            </div>

            {/* Interactive Stage Actions */}
            <div className="pt-2 flex flex-col gap-2">
              {activeStage === 0 && (
                <button
                  type="button"
                  onClick={handleInstantDemoLogin}
                  className="w-full py-2 rounded-xl bg-[#15803d] hover:bg-[#166534] text-white font-mono text-xs font-bold transition-all shadow-sm active:scale-95 flex items-center justify-center gap-1.5"
                >
                  <span>⚡ Quickfill Sarah Chen Credentials</span>
                  <span>→</span>
                </button>
              )}
              {activeStage === 2 && (
                <button
                  type="button"
                  onClick={() => scrollToStage(6)}
                  className="w-full py-2 rounded-xl bg-[#5369d9] hover:bg-[#4052b3] text-white font-mono text-xs font-bold transition-all shadow-sm active:scale-95 flex items-center justify-center gap-1.5"
                >
                  <span>Verify AST Syntax Pass →</span>
                </button>
              )}
              {activeStage === 3 && activeBranch === "clearhire" && (
                <button
                  type="button"
                  onClick={() => {
                    setActiveBranch("legacy");
                    showToast("Switched to Legacy Rejection Route");
                  }}
                  className="w-full py-2 rounded-xl bg-red-600 hover:bg-red-700 text-white font-mono text-xs font-bold transition-all shadow-sm active:scale-95 flex items-center justify-center gap-1.5"
                >
                  <span>Simulate Legacy Heuristic Trap ⚠️</span>
                </button>
              )}
              {activeStage >= 4 && activeStage <= 6 && activeBranch === "legacy" && (
                <button
                  type="button"
                  onClick={() => {
                    setActiveBranch("clearhire");
                    showToast("Switched to ClearHire Covenant Route");
                  }}
                  className="w-full py-2 rounded-xl bg-[#15803d] hover:bg-[#166534] text-white font-mono text-xs font-bold transition-all shadow-sm active:scale-95 flex items-center justify-center gap-1.5"
                >
                  <span>Restore ClearHire Covenant Route ✨</span>
                </button>
              )}
              <button
                type="button"
                onClick={nextStage}
                className="w-full py-1.5 rounded-lg border border-[#24231f]/15 hover:bg-white text-[#706e68] hover:text-[#24231f] font-mono text-[11px] font-semibold transition-all flex items-center justify-center gap-1"
              >
                <span>Advance Journey</span>
                <span>↓</span>
              </button>
            </div>
          </div>
        </aside>
      )}

      {/* 5. Stage 09: Enterprise Candidate Access Portal (Architectural Right-Floating Layout on Desktop) */}
      {activeStage === 8 && (
        <section
          aria-label="Candidate login portal"
          className="fixed inset-0 z-40 flex items-center justify-center lg:justify-end lg:pr-20 px-4 pointer-events-none animate-fadeIn"
        >
          <div className="pointer-events-auto max-w-md w-full p-8 rounded-3xl bg-[#faf7f0]/95 border border-[#24231f]/15 shadow-2xl backdrop-blur-2xl">
            {/* Header */}
            <div className="flex items-center justify-between gap-2 mb-3">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-[#15803d] shadow-[0_0_8px_#15803d]" />
                <span className="font-mono text-xs font-bold uppercase tracking-wider text-[#24231f]">
                  EXECUTIVE DECISION DESK
                </span>
              </div>
              <span className="font-mono text-[10px] text-[#15803d] bg-[#15803d]/10 px-2.5 py-0.5 rounded-full border border-[#15803d]/30 font-bold">
                STAGE 09 FINALE
              </span>
            </div>

            <h1 className="font-serif text-3xl font-bold text-[#24231f] tracking-tight">
              Enter the Candidate Workspace
            </h1>
            <p className="font-sans text-xs text-[#706e68] leading-relaxed mt-1 mb-5">
              Sarah Chen's verified credentials are docked in the executive portfolio under an enforceable 48-Hour SLA covenant.
            </p>

            {/* 1-Click Instant Demo Login Button */}
            <button
              type="button"
              onClick={handleInstantDemoLogin}
              disabled={busy}
              className="w-full py-3.5 mb-5 rounded-2xl font-mono text-xs font-bold bg-[#15803d] hover:bg-[#166534] text-white transition-all flex items-center justify-center gap-2 shadow-lg active:scale-95 disabled:opacity-50"
            >
              <span>{busy ? "AUTHENTICATING..." : "⚡ 1-CLICK INSTANT DEMO ACCESS"}</span>
              <span>→</span>
            </button>

            <div className="flex items-center gap-3 mb-5">
              <div className="flex-1 h-px bg-[#24231f]/10" />
              <span className="font-mono text-[10px] uppercase text-[#706e68]">
                OR DIRECT CREDENTIALS
              </span>
              <div className="flex-1 h-px bg-[#24231f]/10" />
            </div>

            {/* Sign In / Register Tabs */}
            <div className="flex p-1 mb-4 rounded-xl bg-[#eeece2] border border-[#24231f]/10">
              <button
                type="button"
                onClick={() => setAuthMode("signin")}
                className={`flex-1 py-1.5 rounded-lg text-xs font-mono font-bold transition-all ${
                  authMode === "signin"
                    ? "bg-white text-[#24231f] shadow-xs"
                    : "text-[#706e68] hover:text-[#24231f]"
                }`}
              >
                Sign In
              </button>
              <button
                type="button"
                onClick={() => setAuthMode("signup")}
                className={`flex-1 py-1.5 rounded-lg text-xs font-mono font-bold transition-all ${
                  authMode === "signup"
                    ? "bg-white text-[#24231f] shadow-xs"
                    : "text-[#706e68] hover:text-[#24231f]"
                }`}
              >
                Provision Account
              </button>
            </div>

            {/* Error Message */}
            {error && (
              <div className="mb-4 p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-700 text-xs font-mono flex items-center gap-2">
                <span>⚠️</span> {typeof error === "string" ? error : (error?.message || JSON.stringify(error))}
              </div>
            )}

            {/* Credentials Form */}
            <form onSubmit={onSubmit} className="space-y-3.5">
              <div>
                <label className="block font-mono text-[10px] uppercase text-[#706e68] mb-1">
                  Candidate Email
                </label>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="sarah.chen@alum.mit.edu"
                  className="w-full px-3.5 py-2.5 rounded-xl bg-white border border-[#24231f]/15 text-[#24231f] placeholder-[#706e68]/40 text-xs font-mono focus:outline-none focus:border-[#15803d]"
                />
              </div>

              <div>
                <label className="block font-mono text-[10px] uppercase text-[#706e68] mb-1">
                  Password
                </label>
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full px-3.5 py-2.5 rounded-xl bg-white border border-[#24231f]/15 text-[#24231f] placeholder-[#706e68]/40 text-xs font-mono focus:outline-none focus:border-[#15803d]"
                />
              </div>

              {authMode === "signup" && (
                <div>
                  <label className="block font-mono text-[10px] uppercase text-[#706e68] mb-1">
                    Confirm Password
                  </label>
                  <input
                    type="password"
                    required
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="••••••••••••"
                    className="w-full px-3.5 py-2.5 rounded-xl bg-white border border-[#24231f]/15 text-[#24231f] placeholder-[#706e68]/40 text-xs font-mono focus:outline-none focus:border-[#15803d]"
                  />
                </div>
              )}

              <button
                type="submit"
                disabled={busy}
                className="w-full py-3 rounded-xl font-mono text-xs font-bold bg-[#24231f] text-white hover:bg-[#3d3a33] transition-all flex items-center justify-center gap-2 shadow-md active:scale-95 disabled:opacity-50"
              >
                <span>{busy ? "Authenticating..." : authMode === "signin" ? "Enter Workspace" : "Provision Candidate Account"}</span>
                <span>→</span>
              </button>
            </form>
          </div>
        </section>
      )}

      {/* 6. Bottom Navigation Dock (9 Stages) */}
      <nav
        aria-label="Story stage navigation"
        className="fixed bottom-6 left-1/2 -translate-x-1/2 z-40 max-w-[960px] w-[95%] sm:w-auto p-1.5 rounded-full bg-[#faf7f0]/90 border border-[#24231f]/15 backdrop-blur-xl shadow-2xl flex items-center justify-between gap-1"
      >
        <button
          type="button"
          onClick={prevStage}
          disabled={activeStage === 0}
          className="px-3.5 py-1.5 rounded-full font-mono text-xs font-bold transition-all disabled:opacity-25 disabled:cursor-not-allowed hover:bg-[#24231f]/10 active:scale-95 text-[#706e68] hover:text-[#24231f] flex items-center gap-1 shadow-xs"
          title="Previous Stage (Arrow Left / Up)"
        >
          <span>←</span>
          <span className="hidden sm:inline">Prev</span>
        </button>

        <span className="w-px h-4 bg-[#24231f]/15" />

        <div className="flex min-w-0 items-center justify-start md:justify-center gap-1 px-1.5 py-0.5 overflow-x-auto [scrollbar-width:none] [-ms-overflow-style:none] [&::-webkit-scrollbar]:hidden">
          {STORY_STAGES.map((st) => (
            <button
              key={st.index}
              type="button"
              onClick={() => scrollToStage(st.index)}
              title={st.title}
              className={`shrink-0 px-2.5 py-1.5 rounded-full font-mono text-[10px] md:text-[11px] font-semibold transition-all whitespace-nowrap active:scale-95 ${
                activeStage === st.index
                  ? "bg-[#15803d] text-white shadow-md shadow-[#15803d]/30 font-bold"
                  : "text-[#706e68] hover:text-[#24231f] hover:bg-[#24231f]/8"
              }`}
            >
              <span className="md:hidden">{st.num}</span>
              <span className="hidden md:inline">{st.num} {st.shortLabel || st.title.split(" ")[0].toUpperCase()}</span>
            </button>
          ))}
        </div>

        <span className="w-px h-4 bg-[#24231f]/15" />

        <button
          type="button"
          onClick={nextStage}
          disabled={activeStage === 8}
          className="px-3.5 py-1.5 rounded-full font-mono text-xs font-bold transition-all disabled:opacity-25 disabled:cursor-not-allowed hover:bg-[#24231f]/10 active:scale-95 text-[#706e68] hover:text-[#24231f] flex items-center gap-1 shadow-xs"
          title="Next Stage (Arrow Right / Down)"
        >
          <span className="hidden sm:inline">Next</span>
          <span>→</span>
        </button>
      </nav>

      {/* 7. Toast Notification */}
      {toastMessage && (
        <div className="fixed bottom-20 left-1/2 -translate-x-1/2 z-50 px-4 py-2 rounded-full bg-[#24231f] text-white font-mono text-xs font-semibold shadow-xl border border-white/10 animate-bounce">
          {toastMessage}
        </div>
      )}
    </div>
  );
}
