import Link from "next/link";
import { useRouter } from "next/router";
import { useEffect, useState } from "react";
import { getMe } from "../api/auth";
import { clearAuthToken, getStoredAuthToken, setAuthToken } from "../api/client";

const MODULE_LINKS = [
  { href: "/", label: "Mission Control" },
  { href: "/resmat-ai", label: "ResMat.ai" },
  { href: "/jd-analyzer", label: "JD Analyzer" },
  { href: "/job-hunter", label: "Job Hunter" },
  { href: "/student-lab", label: "Student Lab" },
];

export default function ModuleLayout({ title, subtitle, children }) {
  const router = useRouter();
  const [authReady, setAuthReady] = useState(false);
  const [user, setUser] = useState(null);

  useEffect(() => {
    let active = true;

    const bootstrap = async () => {
      const token = getStoredAuthToken();
      if (!token) {
        if (active) {
          setAuthReady(true);
          router.replace("/login");
        }
        return;
      }

      try {
        setAuthToken(token);
        const profile = await getMe();
        if (active) {
          setUser(profile);
        }
      } catch {
        clearAuthToken();
        if (active) {
          router.replace("/login");
        }
      } finally {
        if (active) {
          setAuthReady(true);
        }
      }
    };

    bootstrap();

    return () => {
      active = false;
    };
  }, [router]);

  const onLogout = () => {
    clearAuthToken();
    setUser(null);
    router.push("/login");
  };

  if (!authReady) {
    return (
      <div className="mp-auth-shell">
        <div className="mp-auth-card">
          <h1>Preparing your workspace...</h1>
          <p>Verifying secure access before loading modules.</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <div className="mp-shell">
      <aside className="mp-sidebar">
        <p className="mp-brand-kicker">ClearHire</p>
        <h1 className="mp-brand-title">AI Career Engine</h1>
        <p className="mp-brand-sub">Each module has its own route and focused workflow.</p>

        <nav className="mp-nav">
          {MODULE_LINKS.map((link) => {
            const active = router.pathname === link.href;
            return (
              <Link key={link.href} href={link.href} className={`mp-nav-link ${active ? "active" : ""}`}>
                {link.label}
              </Link>
            );
          })}
        </nav>

        <div className="mp-user-box">
          <p>Signed in as</p>
          <strong>{user.email}</strong>
          <button type="button" onClick={onLogout}>Logout</button>
        </div>
      </aside>

      <main className="mp-main">
        <header className="mp-topbar">
          <h2>{title}</h2>
          <p>{subtitle}</p>
        </header>
        <section className="mp-content">{children}</section>
      </main>
    </div>
  );
}
