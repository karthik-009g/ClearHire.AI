import Link from "next/link";
import { useRouter } from "next/router";
import { useEffect, useRef, useState } from "react";
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
  const loadingCanvasRef = useRef(null);

  useEffect(() => {
    const canvas = loadingCanvasRef.current;
    if (!canvas) {
      return undefined;
    }

    const context = canvas.getContext("2d");
    if (!context) {
      return undefined;
    }

    let width = 0;
    let height = 0;
    let frameId = 0;
    let mouseX = window.innerWidth / 2;
    let mouseY = window.innerHeight / 2;

    const particles = Array.from({ length: 40 }, () => ({
      x: Math.random() * window.innerWidth,
      y: Math.random() * window.innerHeight,
      vx: (Math.random() - 0.5) * 0.22,
      vy: (Math.random() - 0.5) * 0.22,
      base: Math.random() * 0.24 + 0.06,
      r: Math.random() * 1.2 + 0.3,
    }));

    const resize = () => {
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };

    const onMove = (event) => {
      mouseX = event.clientX;
      mouseY = event.clientY;
    };

    const drawFrame = () => {
      context.clearRect(0, 0, width, height);

      const bg = context.createRadialGradient(width * 0.35, height * 0.3, 0, width * 0.5, height * 0.5, width * 0.8);
      bg.addColorStop(0, "hsl(165, 62%, 6%)");
      bg.addColorStop(0.55, "hsl(165, 55%, 4%)");
      bg.addColorStop(1, "#040e10");
      context.fillStyle = bg;
      context.fillRect(0, 0, width, height);

      const ambient = context.createRadialGradient(mouseX, mouseY, 0, mouseX, mouseY, 280);
      ambient.addColorStop(0, "hsla(165, 80%, 70%, 0.06)");
      ambient.addColorStop(1, "transparent");
      context.fillStyle = ambient;
      context.fillRect(0, 0, width, height);

      particles.forEach((particle) => {
        const dx = mouseX - particle.x;
        const dy = mouseY - particle.y;
        const distance = Math.hypot(dx, dy);
        const repel = Math.max(0, 1 - distance / 140);

        if (distance > 0) {
          particle.vx += (-(dx / distance) * repel) * 0.1;
          particle.vy += (-(dy / distance) * repel) * 0.1;
        }

        particle.vx *= 0.97;
        particle.vy *= 0.97;
        particle.x += particle.vx;
        particle.y += particle.vy;

        if (particle.x < 0) particle.x = width;
        if (particle.x > width) particle.x = 0;
        if (particle.y < 0) particle.y = height;
        if (particle.y > height) particle.y = 0;

        const near = Math.max(0, 1 - distance / 170);
        context.beginPath();
        context.arc(particle.x, particle.y, particle.r * (1 + near * 0.65), 0, Math.PI * 2);
        context.fillStyle = `hsla(165, 80%, 70%, ${particle.base + near * 0.32})`;
        context.fill();
      });

      for (let i = 0; i < particles.length; i += 1) {
        for (let j = i + 1; j < particles.length; j += 1) {
          const distance = Math.hypot(particles[i].x - particles[j].x, particles[i].y - particles[j].y);
          if (distance < 90) {
            context.beginPath();
            context.moveTo(particles[i].x, particles[i].y);
            context.lineTo(particles[j].x, particles[j].y);
            context.strokeStyle = `hsla(165, 80%, 70%, ${(1 - distance / 90) * 0.08})`;
            context.lineWidth = 0.45;
            context.stroke();
          }
        }
      }

      frameId = window.requestAnimationFrame(drawFrame);
    };

    resize();
    drawFrame();
    window.addEventListener("resize", resize);
    document.addEventListener("mousemove", onMove);

    return () => {
      window.cancelAnimationFrame(frameId);
      window.removeEventListener("resize", resize);
      document.removeEventListener("mousemove", onMove);
    };
  }, [authReady]);

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
      <div className="mp-prep-screen">
        <canvas ref={loadingCanvasRef} className="mp-prep-canvas" aria-hidden="true" />
        <div className="mp-prep-card">
          <p className="mp-prep-logo">
            clear
            <span>hire</span>
          </p>
          <h1>Preparing your workspace...</h1>
          <p>Verifying secure access before loading modules.</p>
          <div className="mp-prep-load">
            <span className="mp-prep-load-fill" />
          </div>
          <div className="mp-prep-dots" aria-hidden="true">
            <span />
            <span />
            <span />
          </div>
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
        <p className="mp-brand-kicker">
          clear
          <span>hire</span>
        </p>
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
          <button type="button" className="mp-ghost-btn" onClick={onLogout}>Logout</button>
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
