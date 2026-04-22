import { useEffect, useState } from "react";
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

  useEffect(() => {
    setResumeContext(getResmatContext());
    setJdContextState(getJdContext());
  }, []);

  return (
    <ModuleLayout
      title="Mission Control"
      subtitle="Multi-page architecture is active. Open each module in its own route and run the pipeline end-to-end."
    >
      <div className="mp-grid three">
        <article className="mp-card">
          <h3>Resume Ready</h3>
          <p className="mp-metric">{resumeContext?.resumeId ? "Yes" : "No"}</p>
          <p>Resume ID: {resumeContext?.resumeId || "Not set"}</p>
        </article>
        <article className="mp-card">
          <h3>Latest Match</h3>
          <p className="mp-metric">{formatPercent(jdContext?.match?.total_score)}</p>
          <p>Company: {jdContext?.companyName || "Not analyzed"}</p>
        </article>
        <article className="mp-card">
          <h3>Skill Gaps</h3>
          <p className="mp-metric">{jdContext?.skillGap?.length || 0}</p>
          <p>Computed in JD Analyzer route.</p>
        </article>
      </div>

      <div className="mp-grid two">
        {MODULES.map((module) => (
          <article key={module.href} className="mp-card module">
            <h3>{module.title}</h3>
            <p>{module.summary}</p>
            <Link className="mp-link" href={module.href}>
              Open {module.title}
            </Link>
          </article>
        ))}
      </div>
    </ModuleLayout>
  );
}
