import { useEffect, useMemo, useState } from "react";
import ModuleLayout from "../components/ModuleLayout";
import { getJdContext, getResmatContext, normalizeSkills } from "../lib/moduleState";

function buildSprintPlan(skillGap) {
  const gaps = skillGap.length ? skillGap : ["system design", "python", "llm", "docker"];
  return [
    {
      title: "Sprint 1: Core Strength",
      tasks: [`Deep fundamentals of ${gaps[0]}`, `Ship one mini project using ${gaps[0]}`],
    },
    {
      title: "Sprint 2: Applied Build",
      tasks: [`Implement ${gaps[1] || "api engineering"} in a deployable app`, "Write tests and benchmark latency"],
    },
    {
      title: "Sprint 3: Production Readiness",
      tasks: [`Integrate ${gaps[2] || "observability"}`, `Deploy with ${gaps[3] || "docker"} and CI/CD`],
    },
  ];
}

function buildProjectIdeas(skillGap) {
  const a = skillGap[0] || "llm";
  const b = skillGap[1] || "fastapi";
  const c = skillGap[2] || "vector database";

  return [
    `AI resume-to-JD reconciliation service using ${a} + ${b}`,
    `Interview co-pilot that tracks weakness clusters with ${a} analytics`,
    `Job intelligence dashboard with ${c} search and ranking pipeline`,
  ];
}

function buildInterviewDrills(skillGap) {
  const focus = skillGap[0] || "system design";
  return [
    `Design a scalable ${focus} service for 1M users and explain trade-offs.`,
    "Explain one incident postmortem from your own project and remediation plan.",
    "Whiteboard one API workflow from ingestion to ranking with failure paths.",
  ];
}

export default function StudentLabPage() {
  const [resumeContext, setResumeContext] = useState(null);
  const [jdContext, setJdContextState] = useState(null);

  useEffect(() => {
    setResumeContext(getResmatContext());
    setJdContextState(getJdContext());
  }, []);

  const resumeSkills = useMemo(() => normalizeSkills(resumeContext?.parsedSummary?.skills || []), [resumeContext]);
  const skillGap = useMemo(() => normalizeSkills(jdContext?.skillGap || []), [jdContext]);
  const sprints = useMemo(() => buildSprintPlan(skillGap), [skillGap]);
  const projectIdeas = useMemo(() => buildProjectIdeas(skillGap), [skillGap]);
  const interviewDrills = useMemo(() => buildInterviewDrills(skillGap), [skillGap]);

  return (
    <ModuleLayout
      title="Student Lab"
      subtitle="AI engineer growth modules: guided learning sprints, project blueprints, and interview drills."
    >
      <div className="mp-grid two">
        <article className="mp-card">
          <h3>Current Resume Skills</h3>
          <div className="mp-chip-row">
            {resumeSkills.map((skill) => (
              <span key={skill} className="mp-chip">{skill}</span>
            ))}
            {!resumeSkills.length && <p className="mp-muted">Upload a resume in ResMat.ai to populate this.</p>}
          </div>
        </article>

        <article className="mp-card">
          <h3>Priority Skill Gaps</h3>
          <div className="mp-chip-row">
            {skillGap.map((skill) => (
              <span key={skill} className="mp-chip warning">{skill}</span>
            ))}
            {!skillGap.length && <p className="mp-muted">Run JD Analyzer to compute skill gaps first.</p>}
          </div>
        </article>
      </div>

      <div className="mp-grid three">
        {sprints.map((sprint) => (
          <article key={sprint.title} className="mp-card">
            <h3>{sprint.title}</h3>
            <ul className="mp-list compact">
              {sprint.tasks.map((task) => (
                <li key={task}>{task}</li>
              ))}
            </ul>
          </article>
        ))}
      </div>

      <div className="mp-grid two">
        <article className="mp-card">
          <h3>Portfolio Project Ideas</h3>
          <ul className="mp-list compact">
            {projectIdeas.map((idea) => (
              <li key={idea}>{idea}</li>
            ))}
          </ul>
        </article>

        <article className="mp-card">
          <h3>Interview Drill Set</h3>
          <ul className="mp-list compact">
            {interviewDrills.map((drill) => (
              <li key={drill}>{drill}</li>
            ))}
          </ul>
        </article>
      </div>
    </ModuleLayout>
  );
}
