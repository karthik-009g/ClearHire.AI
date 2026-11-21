import Link from "next/link";
import { useRouter } from "next/router";
import { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import { getMe } from "../api/auth";
import { clearAuthToken, getStoredAuthToken, setAuthToken } from "../api/client";

// Dynamically import ClearHireAmbientWorld with ssr: false to prevent SSR hydration mismatches
const ClearHireAmbientWorld = dynamic(
  () => import("./ClearHireAmbientWorld"),
  { ssr: false }
);

const NAV_LINKS = [
  { href: "/", label: "Overview", icon: "✨" },
  { href: "/job-hunter", label: "Direct Requisitions", icon: "🎯" },
  { href: "/applications", label: "Pipeline CRM", icon: "📋" },
  { href: "/resmat-ai", label: "1-Page Resume", icon: "📄" },
  { href: "/jd-analyzer", label: "JD Matcher", icon: "🔍" },
  { href: "/funnel-analytics", label: "Daily Briefing", icon: "📊" },
  { href: "/student-lab", label: "Screener Copilot", icon: "🚀" },
];

export default function ModuleLayout({ title, subtitle, children }) {
  const router = useRouter();
  const [authReady, setAuthReady] = useState(false);
  const [user, setUser] = useState(null);
  const [dbStatus, setDbStatus] = useState("checking");

  // Check live backend/DB connectivity
  useEffect(() => {
    let active = true;
    const checkDb = async () => {
      try {
        const res = await fetch("/ready").catch(() =>
          fetch("http://127.0.0.1:8000/ready")
        );
        if (res && res.ok) {
          if (active) setDbStatus("connected");
        } else {
          if (active) setDbStatus("offline");
        }
      } catch {
        if (active) setDbStatus("offline");
      }
    };
    checkDb();
    const interval = setInterval(checkDb, 25000);
    return () => {
      active = false;
      clearInterval(interval);
    };
  }, []);

  // Check auth session
  useEffect(() => {
    let active = true;
    const checkAuth = async () => {
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
          setAuthReady(true);
        }
      } catch {
        clearAuthToken();
        if (active) router.replace("/login");
      }
    };
    checkAuth();
    return () => {
      active = false;
    };
  }, [router]);

  const onLogout = () => {
    clearAuthToken();
    router.replace("/login");
  };

  if (!authReady || !user) {
    return (
      <div className="clearhire-body min-h-screen bg-[#f6f4ee] flex flex-col items-center justify-center gap-3">
        <div className="w-8 h-8 rounded-full border-2 border-[#5369d9] border-t-transparent animate-spin" />
        <span className="font-mono text-xs text-[#5369d9] uppercase tracking-widest">
          Loading Workspace...
        </span>
      </div>
    );
  }

  return (
    <div className="clearhire-body min-h-screen bg-transparent text-[#24231f] flex flex-col font-sans relative overflow-x-hidden">
      {/* 0. Persistent Three.js Ambient 3D World */}
      <ClearHireAmbientWorld activeRoute={router.pathname} />

      {/* 1. Warm Editorial Header */}
      <header className="sticky top-0 z-40 w-full backdrop-blur-xl bg-[#f6f4ee]/85 border-b border-[#24231f]/10 px-6 py-3.5">
        <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-4">
          {/* Brand */}
          <div className="flex items-center gap-3">
            <Link
              href="/"
              className="text-xl font-bold tracking-tight text-[#24231f] hover:opacity-80 transition-opacity no-underline flex items-baseline gap-0.5"
            >
              clearhire<span className="text-[#5369d9] text-[0.85em]">.ai</span>
            </Link>
            <span className="font-mono text-[9px] text-[#5369d9] bg-[#5369d9]/8 border border-[#5369d9]/25 px-2.5 py-0.5 rounded-full uppercase tracking-wider hidden sm:inline-flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-[#5369d9] animate-pulse" />
              Direct ATS Verified
            </span>
          </div>

          {/* Navigation Pills */}
          <nav className="flex items-center gap-1.5 flex-wrap">
            {NAV_LINKS.map((link) => {
              const active = router.pathname === link.href;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`font-mono text-xs px-3 py-1.5 rounded-full border transition-all flex items-center gap-1.5 no-underline ${
                    active
                      ? "bg-white border-[#5369d9]/35 text-[#5369d9] font-bold shadow-sm"
                      : "bg-white/40 border-[#24231f]/10 text-[#5e5b55] hover:text-[#24231f] hover:bg-white"
                  }`}
                >
                  <span>{link.icon}</span>
                  <span>{link.label}</span>
                </Link>
              );
            })}
          </nav>

          {/* User Session & Logout */}
          <div className="flex items-center gap-2.5">
            <div className="font-mono text-xs px-3 py-1 rounded-full bg-white/60 border border-[#24231f]/12 flex items-center gap-2">
              <span
                className={`w-2 h-2 rounded-full ${
                  dbStatus === "connected" ? "bg-emerald-500" : "bg-amber-500"
                }`}
              />
              <span className="text-[#24231f] text-[11px] hidden md:inline">
                {user.email}
              </span>
            </div>

            <button
              type="button"
              onClick={onLogout}
              className="font-mono text-xs px-3 py-1 rounded-full border border-[#24231f]/15 bg-white/40 text-[#5e5b55] hover:text-[#b91c1c] hover:border-[#b91c1c]/30 hover:bg-red-50/50 transition-all cursor-pointer"
            >
              Sign out ↗
            </button>
          </div>
        </div>
      </header>

      {/* 2. Editorial Section HUD / Banner */}
      {(title || subtitle) && (
        <section className="relative z-10 w-full max-w-7xl mx-auto px-6 pt-6 pb-2">
          <div className="flex flex-wrap items-center justify-between gap-4 p-6 rounded-2xl bg-[#faf7f0]/85 border border-[#24231f]/12 shadow-[0_8px_24px_rgba(36,35,31,0.04)] backdrop-blur-xl">
            <div>
              <div className="font-mono text-[9px] uppercase tracking-widest text-[#706e68] mb-1.5 flex items-center gap-2">
                <span className="w-4 h-[1px] bg-[#bd7652]" />
                <span>ClearHire Workspace</span>
              </div>
              <h1 className="font-serif text-2xl sm:text-3xl font-medium text-[#24231f] tracking-tight m-0">
                {title}
              </h1>
              {subtitle && (
                <p className="text-xs sm:text-sm font-sans text-[#5d5b55] mt-1.5 max-w-2xl leading-relaxed m-0">
                  {subtitle}
                </p>
              )}
            </div>

            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-mono text-[10px] px-3 py-1 rounded-full bg-[#5369d9]/8 border border-[#5369d9]/25 text-[#4052b3] flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-[#5369d9]" />
                40+ Direct Corporate ATS
              </span>
              <span className="font-mono text-[10px] px-3 py-1 rounded-full bg-[#bd7652]/8 border border-[#bd7652]/25 text-[#985b39]">
                🛡️ 14-Day Anti-Ghosting SLA
              </span>
            </div>
          </div>
        </section>
      )}

      {/* 3. Main Workspace Content */}
      <main className="relative z-10 w-full max-w-7xl mx-auto px-6 py-6 flex-1">
        {children}
      </main>

      {/* 4. Editorial Footer */}
      <footer className="relative z-10 w-full max-w-7xl mx-auto px-6 py-5 border-t border-[#24231f]/10 flex items-center justify-between text-xs font-mono text-[#706e68] backdrop-blur-md bg-[#f6f4ee]/60">
        <span>clearhire.ai · A more human way to hire</span>
        <div className="flex items-center gap-4">
          <Link href="/login" className="text-[#5369d9] hover:underline no-underline">
            Story Journey ↑
          </Link>
          <span>·</span>
          <span>FastAPI + PostgreSQL + Next.js</span>
        </div>
      </footer>
    </div>
  );
}
