import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import ModuleLayout from "../components/ModuleLayout";
import { formatPercent, getJdContext, getResmatContext } from "../lib/moduleState";

const MODULES = [
  {
    href: "/resmat-ai",
    title: "ResMat.ai",
    summary: "Resume analyzer with parsing, skills extraction, and skill gap sub-module.",
  },
  {
    href: "/jd-analyzer",
    title: "JD Analyzer",
    summary: "JD + company analysis with resume scoring and generated target tech stack.",
  },
  {
    href: "/job-hunter",
    title: "Job Hunter",
    summary: "Auto-search jobs, match with resume context, and return ranked opportunities.",
  },
  {
    href: "/student-lab",
    title: "Student Lab",
    summary: "AI engineer growth modules: sprints, projects, and interview drills.",
  },
];

export default function HomePage() {
  const [resumeContext, setResumeContext] = useState(null);
  const [jdContext, setJdContextState] = useState(null);
  const canvasRef = useRef(null);

  useEffect(() => {
    setResumeContext(getResmatContext());
    setJdContextState(getJdContext());
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
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
    let hue = 165;

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
      hue = 160 + 16 * Math.sin(Date.now() * 0.00028);

      const bg = context.createRadialGradient(width * 0.35, height * 0.3, 0, width * 0.5, height * 0.5, width * 0.8);
      bg.addColorStop(0, `hsl(${hue}, 62%, 6%)`);
      bg.addColorStop(0.55, `hsl(${hue}, 55%, 4%)`);
      bg.addColorStop(1, "#040e10");
      context.fillStyle = bg;
      context.fillRect(0, 0, width, height);

      const ambient = context.createRadialGradient(mouseX, mouseY, 0, mouseX, mouseY, 280);
      ambient.addColorStop(0, `hsla(${hue}, 100%, 60%, 0.06)`);
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
        context.fillStyle = `hsla(${hue}, 78%, 72%, ${particle.base + near * 0.32})`;
        context.fill();
      });

      for (let i = 0; i < particles.length; i += 1) {
        for (let j = i + 1; j < particles.length; j += 1) {
          const distance = Math.hypot(particles[i].x - particles[j].x, particles[i].y - particles[j].y);
          if (distance < 92) {
            context.beginPath();
            context.moveTo(particles[i].x, particles[i].y);
            context.lineTo(particles[j].x, particles[j].y);
            context.strokeStyle = `hsla(${hue}, 80%, 70%, ${(1 - distance / 92) * 0.08})`;
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
  }, []);

  const rawMatchScore = Number(jdContext?.match?.total_score || 0);
  const matchPercent = Number.isFinite(rawMatchScore)
    ? Math.max(0, Math.min(100, rawMatchScore <= 1 ? rawMatchScore * 100 : rawMatchScore))
    : 0;
  const matchColorClass = matchPercent >= 70 ? "good" : matchPercent >= 50 ? "mid" : "low";

  return (
    <ModuleLayout
      title="Mission Control"
      subtitle="Multi-page architecture is active. Open each module in its own route and run the pipeline end-to-end."
    >
      <canvas ref={canvasRef} className="mp-mission-canvas" aria-hidden="true" />

      <div className="mp-grid three">
        <article className="mp-card mp-stat-card">
          <p className="mp-stat-label">Resume Ready</p>
          <p className="mp-stat-value">{resumeContext?.resumeId ? "Yes" : "No"}</p>
          <p className="mp-stat-meta">Resume ID: {resumeContext?.resumeId || "Not set"}</p>
        </article>
        <article className="mp-card mp-stat-card">
          <p className="mp-stat-label">Latest Match</p>
          <p className={`mp-stat-value ${matchColorClass}`}>{formatPercent(jdContext?.match?.total_score)}</p>
          <div className="mp-match-progress" aria-hidden="true">
            <span style={{ width: `${matchPercent}%` }} />
          </div>
          <p className="mp-stat-meta">Company: {jdContext?.companyName || "Not analyzed"}</p>
        </article>
        <article className="mp-card mp-stat-card">
          <p className="mp-stat-label">Skill Gaps</p>
          <p className="mp-stat-value">{jdContext?.skillGap?.length || 0}</p>
          <p className="mp-stat-meta">Computed in JD Analyzer route.</p>
        </article>
      </div>

      <div className="mp-grid two">
        {MODULES.map((module) => (
          <article key={module.href} className="mp-card module">
            <h3 className="mp-module-title">{module.title}</h3>
            <p className="mp-module-summary">{module.summary}</p>
            <Link className="mp-link mp-link-primary" href={module.href}>
              Open {module.title}
            </Link>
          </article>
        ))}
      </div>
    </ModuleLayout>
  );
}
