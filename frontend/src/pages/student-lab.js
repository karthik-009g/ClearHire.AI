import { useMemo, useState } from "react";
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
  const [materials] = useState(() => ({
    resumeContext: getResmatContext(),
    jdContext: getJdContext(),
  }));
  const { resumeContext, jdContext } = materials;

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
        <article className="mp-card rounded-2xl p-6 bg-[#faf7f0]/85 backdrop-blur-xl border border-[#24231f]/12 shadow-sm">
          <h3>Current Resume Skills</h3>
          <div className="mp-chip-row">
            {resumeSkills.map((skill) => (
              <span key={skill} className="mp-chip">{skill}</span>
            ))}
            {!resumeSkills.length && <p className="mp-muted">Upload a resume in ResMat.ai to populate this.</p>}
          </div>
        </article>

        <article className="mp-card rounded-2xl p-6 bg-[#faf7f0]/85 backdrop-blur-xl border border-[#24231f]/12 shadow-sm">
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
        {sprints.map((sprint, idx) => (
          <article key={sprint.title} className="mp-card rounded-2xl p-6 bg-[#faf7f0]/85 backdrop-blur-xl border border-[#24231f]/12 shadow-sm" style={{ display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                <span style={{ fontSize: "10px", fontFamily: "var(--mono)", color: "var(--brand)", textTransform: "uppercase", letterSpacing: "1px", fontWeight: 700 }}>
                  Sprint 0{idx + 1}
                </span>
                <span style={{ fontSize: "10px", fontFamily: "var(--mono)", color: "#706e68", background: "#eeece2", padding: "2px 8px", borderRadius: "999px" }}>
                  14-Day Cycle
                </span>
              </div>
              <h3 style={{ margin: "0 0 12px 0" }}>{sprint.title}</h3>
              <ul className="mp-list compact" style={{ paddingLeft: 0, listStyle: "none", display: "flex", flexDirection: "column", gap: "8px" }}>
                {sprint.tasks.map((task) => (
                  <li key={task} style={{ display: "flex", alignItems: "flex-start", gap: "8px", fontSize: "13px", color: "#525048" }}>
                    <span style={{ color: "var(--ok)", fontSize: "12px", marginTop: "1px" }}>✓</span>
                    <span>{task}</span>
                  </li>
                ))}
              </ul>
            </div>
          </article>
        ))}
      </div>

      <div className="mp-grid two">
        <article className="mp-card rounded-2xl p-6 bg-[#faf7f0]/85 backdrop-blur-xl border border-[#24231f]/12 shadow-sm">
          <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "12px" }}>
            <span style={{ fontSize: "18px" }}>💡</span>
            <h3 style={{ margin: 0 }}>Portfolio Project Blueprints</h3>
          </div>
          <ul className="mp-list compact" style={{ paddingLeft: 0, listStyle: "none", display: "flex", flexDirection: "column", gap: "10px" }}>
            {projectIdeas.map((idea, idx) => (
              <li
                key={idea}
                style={{
                  display: "flex",
                  alignItems: "flex-start",
                  gap: "10px",
                  padding: "10px 12px",
                  background: "rgba(255, 255, 255, 0.75)",
                  backdropFilter: "blur(12px)",
                  WebkitBackdropFilter: "blur(12px)",
                  borderRadius: "10px",
                  border: "1px solid rgba(36, 35, 31, 0.08)",
                  boxShadow: "0 1px 4px rgba(36, 35, 31, 0.02)",
                  fontSize: "13px",
                  color: "#24231f",
                }}
              >
                <span style={{ fontSize: "10px", fontFamily: "var(--mono)", background: "#eeece2", color: "#706e68", padding: "2px 6px", borderRadius: "4px", flexShrink: 0 }}>
                  0{idx + 1}
                </span>
                <span>{idea}</span>
              </li>
            ))}
          </ul>
        </article>

        <article className="mp-card rounded-2xl p-6 bg-[#faf7f0]/85 backdrop-blur-xl border border-[#24231f]/12 shadow-sm">
          <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "12px" }}>
            <span style={{ fontSize: "18px" }}>🎯</span>
            <h3 style={{ margin: 0 }}>Interview Technical Drills</h3>
          </div>
          <ul className="mp-list compact" style={{ paddingLeft: 0, listStyle: "none", display: "flex", flexDirection: "column", gap: "10px" }}>
            {interviewDrills.map((drill, idx) => (
              <li
                key={drill}
                style={{
                  display: "flex",
                  alignItems: "flex-start",
                  gap: "10px",
                  padding: "10px 12px",
                  background: "rgba(255, 255, 255, 0.75)",
                  backdropFilter: "blur(12px)",
                  WebkitBackdropFilter: "blur(12px)",
                  borderRadius: "10px",
                  border: "1px solid rgba(36, 35, 31, 0.08)",
                  boxShadow: "0 1px 4px rgba(36, 35, 31, 0.02)",
                  fontSize: "13px",
                  color: "#24231f",
                }}
              >
                <span style={{ fontSize: "10px", fontFamily: "var(--mono)", background: "rgba(83, 105, 217, 0.1)", color: "var(--brand)", padding: "2px 6px", borderRadius: "4px", flexShrink: 0 }}>
                  Q{idx + 1}
                </span>
                <span>{drill}</span>
              </li>
            ))}
          </ul>
        </article>
      </div>
    </ModuleLayout>
  );
}
