# ClearHire feature audit — 2026-10-20

This audit maps the current source tree after the additional feature work was discovered. It separates code that has a user path from code that is only an API or prototype. Source inspection does not prove that the app starts, that an external service is configured, or that a remote job is still open.

## Evidence labels

- **VERIFIED IN SOURCE** — the route, component, or behavior is present in this repository.
- **VERIFIED IN PUBLIC DOCS** — an official external document describes the public integration or rule.
- **INFERRED** — likely behavior based on how the source code is connected.
- **UNVERIFIED** — requires a live browser, configured service, credential, or production data to confirm.
- **UNREAD** — an attempted source could not be inspected.

## Feature map

| Area | What is present | State and limits |
|---|---|---|
| Sign-in and workspace | **VERIFIED IN SOURCE:** login, token-based API calls, shared module layout, `/ready` status indicator. | **UNVERIFIED:** no live API/database or deployment was exercised in this pass. The header now reports API/database readiness instead of claiming a specific database vendor. |
| India candidate preferences | **VERIFIED IN SOURCE:** Indian location fields, notice period options (Immediate, 15, 30, 60, 90 days), serving-notice choice, current/expected CTC in LPA, work mode, and Asia/Kolkata scheduling. | Preserved. Values are user preferences; an unset value must remain unknown and must not become an invented answer. |
| Job Hunter | **VERIFIED IN SOURCE:** resume-aware ranking, source and posting-date fields, listing-signal details, location and employer filters, job cards, and a review-first preparation flow. | The user starts each search. Direct ATS discovery is limited to configured boards and companies. Employer-career-page adapters are best-effort HTML readers. Availability, employer ownership, and job freshness still require checking at the employer site. |
| Job-source boundaries | **VERIFIED IN SOURCE:** Greenhouse, Lever, and Ashby are the documented direct ATS adapters currently shown in the product. **VERIFIED IN PUBLIC DOCS:** their public job-posting interfaces are described in their official docs: [Greenhouse Job Board API](https://docs.greenhouse.io/job-board), [Lever Postings API](https://github.com/lever/postings-api/blob/master/README.md), and [Ashby Job Postings API](https://developers.ashbyhq.com/docs/public-job-posting-api). | LinkedIn and Naukri are now manual outbound searches. Their pages are not fetched or scraped by ClearHire. Empty or legacy source selections fall back to the configured direct ATS path, not every adapter at once. |
| Ranking and listing checks | **VERIFIED IN SOURCE:** ranking components and source/date/description/agency signals are returned with the listing. | Scores are heuristics, not a chance of getting hired, employer verification, or response prediction. Agency filtering now excludes an explicit agency marker; an unknown employer is not automatically treated as an agency. |
| Resume and job analysis | **VERIFIED IN SOURCE:** resume upload/version routes, parsing, resume/JD matching, skill gaps, and resume tailoring are available from their pages and API routes. | **UNVERIFIED:** model-provider configuration, embedding quality, PDF rendering, and results on real candidate documents need live checks. |
| Application preparation | **VERIFIED IN SOURCE:** the guided preparation flow can assemble a draft, surface profile fields and screening answers, and require candidate review. | It does not send an application to an employer. External submission is recorded only after the candidate confirms it. |
| Application CRM | **VERIFIED IN SOURCE:** saved application stages, notes, follow-up reminders, review markers, outreach drafts, ATS compatibility, and a browser-fill plan. | Outreach generation is a draft. LinkedIn recruiter search is an outbound link; ClearHire does not automate LinkedIn. |
| Interview preparation | **VERIFIED IN SOURCE:** an application-specific panel uses the exact saved resume version and job description to find text matches and build practice prompts. It labels matches as resume mentions, not verified expertise. It retains Indian recruiter fields and reminds the candidate to confirm them before sharing. | Deterministic term matching, not an interview prediction or independently verified skill assessment. |
| Funnel and digest | **VERIFIED IN SOURCE:** funnel analytics, digest preview, history, and delivery routes. | Email, Telegram, and WhatsApp delivery depend on provider configuration; results distinguish `sent`, `simulated`, `failed`, and `skipped`. Missing recipients no longer become fake destinations. Digest routes require the signed-in owner when authentication is enabled. |
| Browser extension | **VERIFIED IN SOURCE:** the extension now stores a manually entered profile in extension-local storage and fills blank fields on configured ATS hosts. It never submits the employer form, predicts employer response, or inserts a generic answer. Old unversioned fictional fallback profiles are cleared. | The extension is not installed or runtime-verified here. Its field matching is generic and best-effort. The profile is separate from the web app profile until an authenticated integration is built. |
| API keys | **VERIFIED IN SOURCE:** authenticated API-key create/list/revoke routes; the currently supported key scope is read-only. | API-only: no user-facing key-management page and no broader public data API. A key is shown once at creation. |
| Background jobs | **VERIFIED IN SOURCE:** an in-memory queue prototype exists in the code tree. | The public enqueue/status routes are no longer mounted: the queue is process-local, has no registered product jobs, has no per-user ownership model, and previously treated unknown names as successful no-op work. It is not a ClearHire feature until redesigned with persistent storage, ownership, and real handlers. |

## Changes in this pass

1. Removed LinkedIn/Naukri scraping paths and defaults; the Job Hunter keeps manual links to those sites.
2. Changed omitted or stale job-source selections so they do not trigger a scrape across every configured career page.
3. Changed staffing-agency filtering to use a recorded agency marker rather than hiding every job that is not known to be a direct employer.
4. Replaced the fake “Neon DB Active” header with a live API/database readiness state.
5. Improved the shared shell, navigation, funnel rows, and job tabs at tablet and phone widths; reduced canvas particle work on small screens; paused animation in hidden tabs and for reduced-motion preferences.
6. Added application-specific interview preparation using saved resume/JD text and kept unknown India recruiter fields distinct from “No” when preferences are absent.
7. Reworked the browser extension to remove fabricated profiles, hard-coded listing scores, made-up screener answers, fake resume content, and surprise page overlays. The profile is explicit and local, autofill only touches blank fields, and it never submits.
8. Required an authenticated owner for API-key management, limited issued keys to the implemented `read` scope, and unmounted the unsafe background-queue prototype.
9. Tightened resume ownership checks across upload, analysis, version, download, tailoring, export, and expiry cleanup routes. Expiry cleanup is scoped to the authenticated user's own records.
10. Removed invented identity details from PDF export defaults, escaped candidate-provided text before PDF rendering, and isolated the email preview in a sandboxed iframe. Job-feed HTML is escaped and only HTTP(S) application links are clickable.
11. Updated digest delivery feedback so a simulated, skipped, or failed message is not reported as successfully sent; added explicit channel validation and an authentication boundary for personal digest data.

## Visual direction and defensibility

**VERIFIED IN PUBLIC DOCS:** [Igloo](https://igloo.co/expertise/) describes responsive web design, simplifying UX, animation, interactive experiences, and image-loading performance. [Active Theory’s XR experiments](https://xr.activetheory.net/) describes using WebGL/WebXR for cross-platform experiments. [MDN’s WebGL best practices](https://developer.mozilla.org/en-US/docs/Web/API/WebGL_API/WebGL_best_practices) recommends considering a smaller rendering buffer and covers high-DPI rendering; [MDN’s reduced-motion guidance](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/%40media/prefers-reduced-motion) explains how to respond to a system preference. These are design/engineering references, not evidence about ClearHire or permission to copy another site’s code, trade dress, or assets.

**DESIGN CHOICE:** ClearHire keeps an original dark workspace and uses a lightweight ambient canvas, responsive navigation, restrained depth, a capped render scale/particle count, and reduced-motion behavior. It does not add a large WebGL scene to the job workflow; the job search and review controls remain the focus so the mobile workflow stays usable.

For defensible project presentation, preserve original source locations, screenshots, sample inputs, outputs, and timestamps; label observed behavior separately from inference; keep third-party names and design inspiration out of product branding; and avoid claims of Sprout parity, employer verification, or automatic application submission.

## Remaining evidence work before a production claim

- Start the app in a configured environment and verify sign-in, readiness status, job search, resume upload, guided application preparation, interview prep, application stage updates, and digest delivery behavior in a real browser.
- Check each configured company board and record retrieval time, employer URL, posting date when supplied, and whether the destination still accepts applications.
- Review responsive views at phone/tablet/desktop widths and verify that keyboard focus and reduced-motion settings work in the browser.
- Test the extension only on a user-controlled test form first; verify that missing fields stay untouched, missing profile values are skipped, no form is submitted, and no saved profile value leaves extension storage.
- Configure notification providers only when the user intends live delivery; confirm API results distinguish `sent`, `failed`, `simulated`, and `skipped` and verify real recipient/sender handling.
- Build a measured relevance evaluation from candidate-labeled jobs before claiming better ranking quality.


## Deployment repair and runtime evidence — 2026-10-20

The local Compose configuration now points both image builds at the repository root, uses the pgvector-enabled PostgreSQL image required by migration 0006, runs Alembic before starting FastAPI, persists resume files in a named volume, and binds exposed ports to loopback. The frontend uses same-origin API and readiness requests through Next.js rewrites, which avoids browser code depending on a Docker-only service name.

**VERIFIED:** the Next.js production build completed successfully after the proxy and login readiness changes. A locally started standalone Next.js server returned HTTP 200 for /login. The generated route manifest contains /api, /ready, and /health proxy routes.

**UNVERIFIED:** this environment has no Docker CLI, so Compose parsing by Docker, image builds, database migrations, API/database readiness, and full-container end-to-end behavior have not been exercised. The frontend smoke check did not include a running backend. Do not describe the stack as container-verified or production-ready until those checks run on a Docker-enabled machine.

Candidate PDF export now includes a location only when the uploaded resume actually contains one; it no longer substitutes the job location or a generic country.