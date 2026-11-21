# Sprout and ClearHire: evidence-based review

**Scope:** ClearHire source reviewed on 2026-10-20. Sprout evidence includes the user-observed onboarding and a third-party YouTube tutorial, plus Sprout's public marketing and help pages. Those pages establish what Sprout advertises, not its internal architecture or independent proof that every advertised behavior works in production.

## Comparison

| Area | Sprout evidence | ClearHire evidence and tradeoff |
|---|---|---|
| Job discovery | **VERIFIED in user-observed UI:** onboarding collects role, experience, location, salary, and goals; the demo shows a mobile Jobs feed, job cards, and a job-details tour. **VERIFIED as a company claim:** Sprout advertises built-in job search and role matching across mobile and web. | **VERIFIED in code, runtime untested:** Job Hunter uses resume-aware ranking and a card view; the repository implements keyword plus embedding ranking and exposes its component weights, source heuristic, and posting-date availability. ClearHire exposes the ingredients behind its ranking and distinguishes posting date from fetch time; Sprout publicly advertises a more integrated multi-device job-search flow. |
| Application preparation | **VERIFIED in user-provided demo:** AI settings offered review-first and faster modes, with controls for review, Q&A, resume, and cover letter. **VERIFIED as company claims:** Sprout advertises tailored resumes/cover letters, job-specific questions, autofill, and both review-first and quicker submission modes. | **VERIFIED in code, runtime untested:** ClearHire has resume tailoring, an autofill preparation plan, ATS compatibility checks, and a screener-answer service. Its application pipeline requires explicit review and external-submission confirmation. ClearHire currently favors user control; Sprout advertises more automation and a shorter path. |
| Profile and lifecycle | **VERIFIED in user-provided demo:** Profile showed personal information, resume, professional details, and documents; navigation showed Jobs, People, Applications, Emails, and Profile. **VERIFIED as a company claim:** Sprout advertises job tracking and mobile/web access. | **VERIFIED in code/docs, runtime untested:** ClearHire tracks application stages, resume versions, follow-ups, and funnel metrics. Its inspected UI is web-based; the code reviewed here does not establish a mobile app or cross-device sync. |
| Trust | **UNVERIFIED:** the third-party demo does not show how generated answers are grounded or what happens when profile facts are missing. | **VERIFIED in source before this update:** the direct-ATS helper had synthetic fallback openings and fixed low-ghosting scores; the screener helper could invent defaults for notice period and work authorization. Those behaviors weakened trust and were corrected in this pass. |

## ClearHire strengths

- **VERIFIED in code/docs, runtime untested:** explainable resume-to-job matching and skill-gap analysis.
- **VERIFIED in code, runtime untested:** resume versions, tailored materials, application tracking, and human-confirmed external submission.
- **INFERRED:** ClearHire can differentiate through evidence provenance, transparent fit explanations, and candidate control rather than competing on one-swipe volume.

## ClearHire gaps to address

1. **VERIFIED in source:** fabricated fallback openings and unsupported response-risk scores could mislead users. Fix: return only fetched postings and label source heuristics honestly.
2. **VERIFIED in source:** screening answers could assert unknown personal facts. Fix: abstain and ask the candidate to confirm missing data; show only resume-backed facts in drafts.
3. **VERIFIED in requirements and source:** ClearHire is web-first; Sprout demonstrates phone-first onboarding and job cards. ClearHire now has responsive shared navigation and small-screen job/funnel layouts in source; browser verification is still pending.
4. **VERIFIED in code:** application-preparation functions exist as separate controls. Next: organize them into candidate-selected modes: review every artifact, draft quickly but review before external submission, or use the original resume with a reviewed cover letter.
5. **INFERRED:** response prediction should remain out of the product until ClearHire has enough outcome data to evaluate it. Show “no update after 14 days” as a follow-up reminder, not an employer prediction.

## Product defensibility

Build ClearHire as an independent product. Do not copy Sprout's brand, screen styling, or exact interaction design. A defensible implementation should retain the source URL and capture time for each job, show the evidence behind fit and generated claims, preserve each resume/application version, log candidate review/approval, and evaluate match quality against labeled examples. Never claim job availability, employer legitimacy, or response likelihood without evidence.

## Evidence sources

- User-observed Sprout tutorial: [How to Use Sprout AI to Auto Apply for Jobs and Save Time on Applications](https://www.youtube.com/watch?v=iAHM7BZMlvE) (third-party demonstration).
- Sprout company feature claims: [AI job applications](https://www.usesprout.com/features/ai-job-application), [AI Apply](https://www.usesprout.com/features/ai-apply), and [Profile Analysis](https://www.usesprout.com/features/profile-analysis).
- Sprout help documentation: [getting started](https://help.usesprout.com/en/articles/11639790-welcome-to-sprout-how-to-get-started), [choosing the resume and cover letter sent](https://help.usesprout.com/en/articles/17155048-choosing-which-resume-and-cover-letter-get-sent), and [how applying works](https://help.usesprout.com/en/articles/11676023-how-do-i-apply-to-jobs-on-sprout).
- These pages are evidence of published claims and documented workflows. They are not proof of Sprout's internal design or a successful end-to-end production run.

## ClearHire implementation update — guided application preparation

The next product slice now connects Job Hunter to the existing application pipeline and makes listing freshness/ranking inputs auditable:

1. Open a job workspace showing the saved source link, opportunity ranking, its four weighted components, source-reported listing date, fetch time, and exact resume-skill phrases also present in the listing. Text overlap is labeled as evidence, not a claim that the candidate meets every requirement.
2. Choose the latest resume or create a job-tailored version with a cover-letter draft.
3. Review and edit profile fields, inspect the resume excerpts, and request drafts for job-specific screening questions. Screening drafts show their supporting facts and require the candidate to confirm each answer before review.
4. Save a draft with the source URL and resume version. If profile readiness is incomplete, the record stays `review_required`.
5. Confirm the review, open the employer's own site, and record submission only after confirming the external application was actually sent.

Source-reported listing dates are persisted separately from retrieval time; invalid or missing source dates stay unknown and receive a neutral freshness component. Candidate-specific ranking scores are computed per search and are not stored on shared job postings. The score is labeled a heuristic ranking, not a probability of getting hired.

Manual and scheduled searches now apply saved or current location preferences; common Indian/US location aliases are recognized. Direct ATS searches use Indian/remote filtering by default and broaden when a non-India location is selected. Scheduled searches also honor saved target companies, freshness, employer-source, agency, and listing-risk filters. The review panel retains saved Indian preferences: city/remote locations, notice period, serving-notice choice, current and expected CTC in ₹ LPA, work mode, and India time zone. The existing notice options remain immediate, 15, 30, 60, and 90 days; no notice period is preselected for a new profile. Scheduled sourcing, login-triggered sourcing, and email-after-search are explicit settings rather than being silently enabled on save.

The flow reuses the existing versioned resume, screener, application review, and submission-log endpoints. It does not send an application to an employer. Repeated preparation of the same saved listing reuses the existing application record. Application and resume ownership checks now reject anonymous access when authentication is enabled. Job search also respects selected filters instead of silently returning postings that failed those filters.

**Completion status:** source changes are in place; browser/runtime behavior and the generated frontend bundle have not yet been verified. The scoring now uses source-reported dates when available and a neutral value when not, but relevance quality still needs labeled-job evaluation. The missing 0007 and 0008 revisions were recovered from the nested job_automate checkout and copied into the main backend; the nested checkout was left untouched. Alembic history and offline SQL generation passed in the earlier pass. Subsequent source work also removed fake notification/PDF recipients and candidate identity defaults, enforced resume and digest ownership when authentication is enabled, scoped retention cleanup to the current user, escaped untrusted digest/PDF content, and marked email previews as sandboxed. No database upgrade, browser run, full build, or test suite has been performed in this pass. Do not claim production readiness or Sprout parity until these checks are complete.

