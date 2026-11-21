// ClearHire.AI Background Service Worker (Manifest V3)

const DEFAULT_BACKEND_URL = "http://localhost:8000";

// Fetch candidate profile from local storage or backend
async function getCandidateProfile() {
  const data = await chrome.storage.local.get(["clearhire_profile", "clearhire_backend_url"]);
  if (data.clearhire_profile) {
    return data.clearhire_profile;
  }

  const backendUrl = data.clearhire_backend_url || DEFAULT_BACKEND_URL;
  try {
    const res = await fetch(`${backendUrl}/api/jobs/preferences`);
    if (res.ok) {
      const pref = await res.json();
      const profile = {
        fullName: "Candidate User",
        email: pref.preferred_email || "candidate@clearhire.ai",
        phone: "+91 9876543210",
        location: pref.locations?.[0] || "Bengaluru, India",
        linkedin: "https://linkedin.com/in/candidate",
        github: "https://github.com/candidate",
        portfolio: "https://candidate.dev",
        noticePeriodDays: pref.notice_period_days !== null ? pref.notice_period_days : 30,
        servingNotice: Boolean(pref.serving_notice),
        currentCtcLpa: pref.current_ctc_lpa || 24.0,
        expectedCtcLpa: pref.expected_ctc_lpa || 36.0,
        workMode: pref.work_mode || "hybrid",
        workAuthorization: "Yes, authorized to work in India",
        gender: "Prefer not to say",
      };
      await chrome.storage.local.set({ clearhire_profile: profile });
      return profile;
    }
  } catch (err) {
    console.debug("Backend offline, returning fallback candidate profile:", err);
  }

  // Sensible default fallback profile
  const fallback = {
    fullName: "Alex Sharma",
    email: "candidate@clearhire.ai",
    phone: "+91 9876543210",
    location: "Bengaluru, Karnataka, India",
    linkedin: "https://linkedin.com/in/alexsharma",
    github: "https://github.com/alexsharma",
    portfolio: "https://alexsharma.dev",
    noticePeriodDays: 30,
    servingNotice: true,
    currentCtcLpa: 26.0,
    expectedCtcLpa: 38.0,
    workMode: "hybrid",
    workAuthorization: "Yes",
    gender: "Prefer not to say",
  };
  await chrome.storage.local.set({ clearhire_profile: fallback });
  return fallback;
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === "GET_PROFILE") {
    getCandidateProfile().then((profile) => {
      sendResponse({ success: true, profile });
    }).catch((err) => {
      sendResponse({ success: false, error: err.message });
    });
    return true; // Keep channel open for async response
  }

  if (message.action === "SAVE_PROFILE") {
    chrome.storage.local.set({ clearhire_profile: message.profile }).then(() => {
      sendResponse({ success: true });
    });
    return true;
  }

  if (message.action === "ANALYZE_PAGE_URL") {
    const url = message.url || "";
    let atsProvider = null;
    let authenticityScore = 65;
    let ghostingRisk = "medium";

    if (url.includes("greenhouse.io")) {
      atsProvider = "Greenhouse";
      authenticityScore = 95;
      ghostingRisk = "low";
    } else if (url.includes("lever.co")) {
      atsProvider = "Lever";
      authenticityScore = 92;
      ghostingRisk = "low";
    } else if (url.includes("ashbyhq.com")) {
      atsProvider = "Ashby";
      authenticityScore = 94;
      ghostingRisk = "low";
    } else if (url.includes("myworkdayjobs.com")) {
      atsProvider = "Workday";
      authenticityScore = 88;
      ghostingRisk = "low";
    } else if (url.includes("darwinbox.in")) {
      atsProvider = "Darwinbox";
      authenticityScore = 90;
      ghostingRisk = "low";
    } else if (url.includes("linkedin.com")) {
      atsProvider = "LinkedIn";
      authenticityScore = 60;
      ghostingRisk = "medium";
    }

    sendResponse({
      atsProvider,
      authenticityScore,
      ghostingRisk,
      isDirectEmployer: Boolean(atsProvider && atsProvider !== "LinkedIn"),
    });
    return true;
  }

  if (message.action === "ANSWER_SCREENER") {
    chrome.storage.local.get(["clearhire_backend_url"]).then(async (data) => {
      const backendUrl = data.clearhire_backend_url || DEFAULT_BACKEND_URL;
      try {
        const res = await fetch(`${backendUrl}/api/applications/answer-screener`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            question: message.question,
            company: message.company,
            role: message.role,
            max_words: message.max_words || 150,
          }),
        });

        if (res.ok) {
          const payload = await res.json();
          sendResponse({ success: true, answer: payload.answer, intent: payload.detected_intent });
        } else {
          sendResponse({
            success: true,
            answer: `With extensive background in backend engineering, distributed architectures, and agile product development, I bring proven execution skills and strong ownership to ${message.company || "your team"}.`,
          });
        }
      } catch (err) {
        sendResponse({
          success: true,
          answer: `I am deeply interested in contributing my skills in scalable backend engineering and performance optimization to ${message.company || "your organization"}.`,
        });
      }
    });
    return true;
  }
});

