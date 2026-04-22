"""Configuration and constants for the free resume analyzer."""

MAX_MISSING_KEYWORDS = 15
DEFAULT_TARGET_ROLE = "Software Engineer"

SECTION_HINTS = {
    "contact": ["@", "linkedin", "github", "phone", "mobile"],
    "education": ["education", "bachelor", "master", "university", "college"],
    "experience": ["experience", "work", "employment", "internship"],
    "skills": ["skills", "tech stack", "technologies", "tools"],
    "projects": ["projects", "portfolio", "case study"],
}
