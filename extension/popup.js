// ClearHire.AI Extension Popup Controller

document.addEventListener("DOMContentLoaded", async () => {
  const atsNameEl = document.getElementById("ats-name");
  const ghostingBadgeEl = document.getElementById("ghosting-badge");
  const authScoreEl = document.getElementById("authenticity-score");
  const candNameEl = document.getElementById("cand-name");
  const candNoticeEl = document.getElementById("cand-notice");
  const candCtcEl = document.getElementById("cand-ctc");
  const statusMsgEl = document.getElementById("status-msg");
  const btnAutofill = document.getElementById("btn-autofill");
  const btnCopyProfile = document.getElementById("btn-copy-profile");

  let currentProfile = null;

  // 1. Load active tab and analyze page
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tab && tab.url) {
      chrome.runtime.sendMessage({ action: "ANALYZE_PAGE_URL", url: tab.url }, (analysis) => {
        if (analysis) {
          atsNameEl.innerText = analysis.atsProvider || "Standard Web Portal";
          authScoreEl.innerText = `${analysis.authenticityScore}%`;

          if (analysis.ghostingRisk === "low") {
            ghostingBadgeEl.className = "badge badge-low";
            ghostingBadgeEl.innerText = "🟢 Low Ghosting Risk";
          } else if (analysis.ghostingRisk === "high") {
            ghostingBadgeEl.className = "badge badge-high";
            ghostingBadgeEl.innerText = "🔴 High Ghosting Risk";
          } else {
            ghostingBadgeEl.className = "badge badge-med";
            ghostingBadgeEl.innerText = "🟡 Medium Ghosting Risk";
          }
        }
      });
    }
  } catch (err) {
    console.debug("Could not inspect active tab:", err);
  }

  // 2. Load candidate profile
  chrome.runtime.sendMessage({ action: "GET_PROFILE" }, (response) => {
    if (response && response.success && response.profile) {
      currentProfile = response.profile;
      candNameEl.innerText = currentProfile.fullName || "Candidate User";
      candNoticeEl.innerText = `${currentProfile.noticePeriodDays} Days${currentProfile.servingNotice ? " (Serving)" : ""}`;
      candCtcEl.innerText = currentProfile.expectedCtcLpa ? `${currentProfile.expectedCtcLpa} LPA` : "Not specified";
    }
  });

  // 3. Handle 1-Click Autofill
  btnAutofill.addEventListener("click", async () => {
    statusMsgEl.innerText = "Filling form fields...";
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (!tab?.id) {
        statusMsgEl.innerText = "No active tab found.";
        return;
      }

      chrome.tabs.sendMessage(tab.id, { action: "TRIGGER_AUTOFILL" }, (res) => {
        if (chrome.runtime.lastError) {
          statusMsgEl.innerText = "Please refresh the job page first.";
          return;
        }

        if (res && res.success) {
          statusMsgEl.innerText = `✓ Successfully filled ${res.count} fields!`;
        } else {
          statusMsgEl.innerText = res?.error || "No compatible fields detected.";
        }
      });
    } catch (err) {
      statusMsgEl.innerText = `Error: ${err.message}`;
    }
  });

  const btnDownloadPdf = document.getElementById("btn-download-pdf");

  // 4. Handle Download ATS PDF
  btnDownloadPdf?.addEventListener("click", async () => {
    statusMsgEl.innerText = "Compiling ATS 1-page PDF...";
    try {
      const resumeText = currentProfile?.tailoredResumeText || 
        "## TECHNICAL SKILLS\nPython, FastAPI, Docker, PostgreSQL, Distributed Systems\n\n## EXPERIENCE\nBackend Engineer\n- Built scalable APIs and high throughput services.";

      const res = await fetch("http://localhost:8000/api/resumes/export-pdf", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          resume_text: resumeText,
          candidate_name: currentProfile?.fullName || "Candidate",
          contact_line: `${currentProfile?.email || "candidate@clearhire.ai"} | ${currentProfile?.location || "Bengaluru, India"}`,
        }),
      });

      if (!res.ok) throw new Error("Backend PDF compiler unavailable");

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "ClearHire_ATS_Tailored_Resume.pdf";
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      statusMsgEl.innerText = "✓ PDF downloaded successfully!";
    } catch (err) {
      statusMsgEl.innerText = "Could not download PDF. Is backend running?";
    }
  });

  // 5. Handle AI Recruiter InMail & Search
  const btnDraftOutreach = document.getElementById("btn-draft-outreach");
  btnDraftOutreach?.addEventListener("click", async () => {
    statusMsgEl.innerText = "Drafting recruiter outreach...";
    try {
      const company = atsNameEl?.innerText && atsNameEl.innerText !== "Detecting..." ? atsNameEl.innerText : "the company";
      const res = await fetch("http://localhost:8000/api/applications/outreach", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          company: company,
          role: "Software Engineer",
          candidate_name: currentProfile?.fullName || "Candidate",
        }),
      });
      if (!res.ok) throw new Error("Outreach drafter unavailable");
      const data = await res.json();
      navigator.clipboard.writeText(data.hiring_manager_inmail);
      statusMsgEl.innerText = "✓ InMail copied! Opening recruiter search...";
      if (data.linkedin_recruiter_search_url && chrome.tabs) {
        chrome.tabs.create({ url: data.linkedin_recruiter_search_url });
      }
    } catch (err) {
      statusMsgEl.innerText = "Could not draft outreach. Backend active?";
    }
  });

  // 6. Handle Copy Profile JSON
  btnCopyProfile.addEventListener("click", () => {
    if (currentProfile) {
      navigator.clipboard.writeText(JSON.stringify(currentProfile, null, 2));
      statusMsgEl.innerText = "Profile JSON copied to clipboard!";
      setTimeout(() => {
        statusMsgEl.innerText = "";
      }, 2500);
    }
  });
});
