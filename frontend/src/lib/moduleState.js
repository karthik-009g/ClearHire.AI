const RESMAT_CONTEXT_KEY = "clearhire_resmat_context";
const JD_CONTEXT_KEY = "clearhire_jd_context";

const KNOWN_SKILLS = [
  "python",
  "java",
  "javascript",
  "typescript",
  "react",
  "next.js",
  "node.js",
  "fastapi",
  "django",
  "flask",
  "sql",
  "postgresql",
  "mongodb",
  "redis",
  "docker",
  "kubernetes",
  "aws",
  "azure",
  "gcp",
  "machine learning",
  "deep learning",
  "nlp",
  "llm",
  "langchain",
  "langgraph",
  "airflow",
  "spark",
  "etl",
  "git",
  "linux",
  "rest api",
  "microservices",
  "ci/cd",
  "pytest",
  "pandas",
  "numpy",
  "scikit-learn",
  "tensorflow",
  "pytorch",
  "prompt engineering",
  "vector database",
  "pgvector",
  "system design",
];

function isBrowser() {
  return typeof window !== "undefined";
}

function readJson(key, fallback) {
  if (!isBrowser()) {
    return fallback;
  }

  try {
    const raw = window.localStorage.getItem(key);
    if (!raw) {
      return fallback;
    }
    return JSON.parse(raw);
  } catch {
    return fallback;
  }
}

function writeJson(key, value) {
  if (!isBrowser()) {
    return;
  }

  window.localStorage.setItem(key, JSON.stringify(value));
}

export function getResmatContext() {
  return readJson(RESMAT_CONTEXT_KEY, null);
}

export function setResmatContext(context) {
  writeJson(RESMAT_CONTEXT_KEY, context);
}

export function clearResmatContext() {
  if (!isBrowser()) {
    return;
  }
  window.localStorage.removeItem(RESMAT_CONTEXT_KEY);
}

export function getJdContext() {
  return readJson(JD_CONTEXT_KEY, null);
}

export function setJdContext(context) {
  writeJson(JD_CONTEXT_KEY, context);
}

export function clearJdContext() {
  if (!isBrowser()) {
    return;
  }
  window.localStorage.removeItem(JD_CONTEXT_KEY);
}

export function formatPercent(score) {
  if (typeof score !== "number" || Number.isNaN(score)) {
    return "--";
  }
  const scaled = score <= 1 ? score * 100 : score;
  return `${Math.round(scaled)}%`;
}

export function parseCsv(text) {
  return (text || "")
    .split(",")
    .map((value) => value.trim())
    .filter(Boolean);
}

export function normalizeSkills(skills) {
  if (!Array.isArray(skills)) {
    return [];
  }

  const seen = new Set();
  const normalized = [];

  for (const skill of skills) {
    const clean = String(skill || "").trim();
    if (!clean) {
      continue;
    }

    const key = clean.toLowerCase();
    if (seen.has(key)) {
      continue;
    }

    seen.add(key);
    normalized.push(clean);
  }

  return normalized;
}

export function extractSkillKeywords(text) {
  const lower = String(text || "").toLowerCase();
  if (!lower) {
    return [];
  }

  const found = KNOWN_SKILLS.filter((skill) => lower.includes(skill));
  return normalizeSkills(found);
}

export function inferTargetSkills(jdText, jobs = []) {
  const merged = new Set(extractSkillKeywords(jdText).map((skill) => skill.toLowerCase()));

  for (const job of jobs) {
    const candidateText = `${job?.title || ""} ${job?.company || ""}`;
    for (const skill of extractSkillKeywords(candidateText)) {
      merged.add(skill.toLowerCase());
    }
  }

  return Array.from(merged)
    .map((skill) => KNOWN_SKILLS.find((entry) => entry.toLowerCase() === skill) || skill)
    .map((skill) => String(skill))
    .slice(0, 20);
}

export function computeSkillGap(resumeSkills, targetSkills) {
  const resumeSet = new Set(normalizeSkills(resumeSkills).map((skill) => skill.toLowerCase()));
  return normalizeSkills(targetSkills).filter((skill) => !resumeSet.has(skill.toLowerCase()));
}
