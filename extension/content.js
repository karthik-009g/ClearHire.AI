// ClearHire.AI Content Script: In-Page DOM Autofill Engine & Anti-Ghosting Indicator
(() => {
  // Prevent double-injection
  if (window.__clearhire_injected) return;
  window.__clearhire_injected = true;

  console.log("🛡️ ClearHire.AI Smart Autofill & Ghosting Shield initialized.");

  // Helper to safely trigger React/Angular input change events
  function setNativeValue(element, value) {
    if (!element) return;
    const valueSetter = Object.getOwnPropertyDescriptor(element, "value")?.set;
    const prototype = Object.getPrototypeOf(element);
    const prototypeValueSetter = Object.getOwnPropertyDescriptor(prototype, "value")?.set;

    if (prototypeValueSetter && valueSetter !== prototypeValueSetter) {
      prototypeValueSetter.call(element, value);
    } else if (valueSetter) {
      valueSetter.call(element, value);
    } else {
      element.value = value;
    }

    element.dispatchEvent(new Event("input", { bubbles: true }));
    element.dispatchEvent(new Event("change", { bubbles: true }));
    element.dispatchEvent(new Event("blur", { bubbles: true }));
    element.style.boxShadow = "0 0 0 2px #66e9ad";
  }

  // Field matcher heuristics
  function findFieldByKeywords(keywords) {
    const selector = "input:not([type='hidden']):not([type='submit']):not([type='button']), textarea, select";
    const elements = Array.from(document.querySelectorAll(selector));

    for (const el of elements) {
      const id = (el.id || "").toLowerCase();
      const name = (el.name || "").toLowerCase();
      const placeholder = (el.placeholder || "").toLowerCase();
      const ariaLabel = (el.getAttribute("aria-label") || "").toLowerCase();
      const dataAutomation = (el.getAttribute("data-automation-id") || "").toLowerCase();

      // Find label text if any
      let labelText = "";
      if (el.id) {
        const labelEl = document.querySelector(`label[for="${el.id}"]`);
        if (labelEl) labelText = labelEl.innerText.toLowerCase();
      }
      if (!labelText && el.closest("label")) {
        labelText = el.closest("label").innerText.toLowerCase();
      }

      const combined = `${id} ${name} ${placeholder} ${ariaLabel} ${dataAutomation} ${labelText}`;

      for (const kw of keywords) {
        if (combined.includes(kw.toLowerCase())) {
          return el;
        }
      }
    }
    return null;
  }

  // Fill form fields
  function autofillForm(profile) {
    let filledCount = 0;

    // 1. First Name
    const firstName = profile.fullName?.split(" ")[0] || "";
    const firstEl = findFieldByKeywords(["first_name", "firstname", "first name", "given name", "first-name"]);
    if (firstEl && !firstEl.value) {
      setNativeValue(firstEl, firstName);
      filledCount++;
    }

    // 2. Last Name
    const lastName = profile.fullName?.split(" ").slice(1).join(" ") || "";
    const lastEl = findFieldByKeywords(["last_name", "lastname", "last name", "family name", "surname"]);
    if (lastEl && !lastEl.value) {
      setNativeValue(lastEl, lastName);
      filledCount++;
    }

    // 3. Full Name (if no first/last separate)
    if (!firstEl && !lastEl) {
      const fullEl = findFieldByKeywords(["full_name", "fullname", "full name", "applicant_name", "candidate_name", "name"]);
      if (fullEl && !fullEl.value) {
        setNativeValue(fullEl, profile.fullName);
        filledCount++;
      }
    }

    // 4. Email
    const emailEl = findFieldByKeywords(["email", "e-mail", "email_address", "electronic mail"]);
    if (emailEl && !emailEl.value) {
      setNativeValue(emailEl, profile.email);
      filledCount++;
    }

    // 5. Phone
    const phoneEl = findFieldByKeywords(["phone", "mobile", "telephone", "contact_number", "cell"]);
    if (phoneEl && !phoneEl.value) {
      setNativeValue(phoneEl, profile.phone);
      filledCount++;
    }

    // 6. Location / Address
    const locEl = findFieldByKeywords(["location", "city", "address", "current_location"]);
    if (locEl && !locEl.value) {
      setNativeValue(locEl, profile.location);
      filledCount++;
    }

    // 7. LinkedIn
    const liEl = findFieldByKeywords(["linkedin", "linked_in", "linkedin_profile", "linkedin_url"]);
    if (liEl && !liEl.value) {
      setNativeValue(liEl, profile.linkedin);
      filledCount++;
    }

    // 8. GitHub
    const ghEl = findFieldByKeywords(["github", "git_hub", "github_profile", "github_url"]);
    if (ghEl && !ghEl.value) {
      setNativeValue(ghEl, profile.github);
      filledCount++;
    }

    // 9. Portfolio / Website
    const portEl = findFieldByKeywords(["portfolio", "website", "personal_website", "blog"]);
    if (portEl && !portEl.value) {
      setNativeValue(portEl, profile.portfolio);
      filledCount++;
    }

    // 10. Notice Period (India market)
    const noticeEl = findFieldByKeywords(["notice", "notice_period", "notice period", "availability"]);
    if (noticeEl) {
      if (noticeEl.tagName === "SELECT") {
        for (const opt of noticeEl.options) {
          if (opt.text.toLowerCase().includes("30") || opt.text.toLowerCase().includes("month") || opt.text.toLowerCase().includes("immediate")) {
            noticeEl.value = opt.value;
            noticeEl.dispatchEvent(new Event("change", { bubbles: true }));
            filledCount++;
            break;
          }
        }
      } else if (!noticeEl.value) {
        setNativeValue(noticeEl, `${profile.noticePeriodDays} days${profile.servingNotice ? " (Serving Notice)" : ""}`);
        filledCount++;
      }
    }

    // 11. CTC (LPA)
    const ctcEl = findFieldByKeywords(["ctc", "current_salary", "current ctc", "compensation"]);
    if (ctcEl && !ctcEl.value) {
      setNativeValue(ctcEl, `${profile.currentCtcLpa} LPA`);
      filledCount++;
    }

    const expCtcEl = findFieldByKeywords(["expected_ctc", "expected_salary", "expected compensation"]);
    if (expCtcEl && !expCtcEl.value) {
      setNativeValue(expCtcEl, `${profile.expectedCtcLpa} LPA`);
      filledCount++;
    }

    return filledCount;
  }

  // Inject floating ClearHire autofill badge into the page
  function injectFloatingBadge() {
    if (document.getElementById("clearhire-floating-badge")) return;

    const host = window.location.hostname;
    let atsName = "Direct Portal";
    if (host.includes("greenhouse.io")) atsName = "Greenhouse ATS";
    else if (host.includes("lever.co")) atsName = "Lever ATS";
    else if (host.includes("ashbyhq.com")) atsName = "Ashby ATS";
    else if (host.includes("myworkdayjobs.com")) atsName = "Workday";
    else if (host.includes("darwinbox.in")) atsName = "Darwinbox";
    else if (host.includes("linkedin.com")) atsName = "LinkedIn Direct";

    const badge = document.createElement("div");
    badge.id = "clearhire-floating-badge";
    badge.style.cssText = `
      position: fixed;
      bottom: 24px;
      right: 24px;
      z-index: 999999;
      background: #082542;
      border: 1px solid rgba(123, 182, 236, 0.4);
      border-radius: 12px;
      box-shadow: 0 10px 30px rgba(0,0,0,0.5);
      padding: 12px 16px;
      display: flex;
      align-items: center;
      gap: 12px;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      color: #e9f5ff;
      font-size: 13px;
      backdrop-filter: blur(10px);
      transition: transform 0.2s ease;
    `;

    badge.innerHTML = `
      <div style="display: flex; align-items: center; gap: 8px;">
        <span style="font-size: 18px;">🛡️</span>
        <div>
          <strong style="color: #66e9ad; display: block; font-size: 12px;">ClearHire Shield • ${atsName}</strong>
          <span style="color: #b7d7f2; font-size: 11px;">Low Ghosting Risk (Verified Direct)</span>
        </div>
      </div>
      <button id="clearhire-autofill-btn" style="
        background: linear-gradient(135deg, #16a34a, #22c55e);
        border: none;
        color: white;
        font-weight: 700;
        font-size: 12px;
        padding: 8px 14px;
        border-radius: 8px;
        cursor: pointer;
        box-shadow: 0 2px 8px rgba(34, 197, 94, 0.4);
        display: flex;
        align-items: center;
        gap: 6px;
      ">
        ⚡ 1-Click Autofill
      </button>
      <button id="clearhire-close-badge" style="
        background: transparent;
        border: none;
        color: #8ab6d6;
        font-size: 14px;
        cursor: pointer;
        padding: 2px 4px;
      ">✕</button>
    `;

    document.body.appendChild(badge);

    document.getElementById("clearhire-close-badge")?.addEventListener("click", () => {
      badge.remove();
    });

    document.getElementById("clearhire-autofill-btn")?.addEventListener("click", () => {
      const btn = document.getElementById("clearhire-autofill-btn");
      if (btn) btn.innerText = "Filling...";

      chrome.runtime.sendMessage({ action: "GET_PROFILE" }, (response) => {
        if (response && response.success && response.profile) {
          const count = autofillForm(response.profile);
          if (btn) {
            btn.innerText = `✓ Filled ${count} Fields!`;
            setTimeout(() => {
              if (btn) btn.innerText = "⚡ 1-Click Autofill";
            }, 3000);
          }
        } else {
          if (btn) btn.innerText = "Error loading profile";
        }
      });
    });
  }

  // Inject AI Screener Answer chips above textareas
  function injectScreenerChips() {
    const textareas = document.querySelectorAll("textarea:not([data-clearhire-chip])");
    for (const ta of textareas) {
      ta.setAttribute("data-clearhire-chip", "true");

      let questionText = ta.placeholder || "";
      if (ta.id) {
        const label = document.querySelector(`label[for="${ta.id}"]`);
        if (label) questionText = label.innerText.trim();
      }
      if (!questionText && ta.closest("label")) {
        questionText = ta.closest("label").innerText.trim();
      }
      if (!questionText) {
        const prev = ta.previousElementSibling;
        if (prev && (prev.tagName === "LABEL" || prev.tagName === "H3" || prev.tagName === "P" || prev.tagName === "SPAN")) {
          questionText = prev.innerText.trim();
        }
      }

      const chip = document.createElement("button");
      chip.type = "button";
      chip.className = "clearhire-screener-chip";
      chip.innerText = "✨ Answer with ClearHire AI";
      chip.style.cssText = `
        display: inline-flex;
        align-items: center;
        gap: 4px;
        background: rgba(47, 179, 255, 0.15);
        color: #51d2ff;
        border: 1px solid rgba(47, 179, 255, 0.4);
        border-radius: 6px;
        padding: 4px 10px;
        font-size: 11px;
        font-weight: 600;
        cursor: pointer;
        margin-bottom: 6px;
        transition: all 0.15s ease;
      `;

      chip.addEventListener("click", (e) => {
        e.preventDefault();
        chip.innerText = "Generating Grounded Answer...";
        chrome.runtime.sendMessage(
          {
            action: "ANSWER_SCREENER",
            question: questionText || "Why do you want to join this company and how does your experience align?",
            company: document.title || "",
          },
          (res) => {
            if (res && res.answer) {
              setNativeValue(ta, res.answer);
              chip.innerText = "✓ Answer Injected!";
              setTimeout(() => {
                chip.innerText = "✨ Re-Answer with ClearHire AI";
              }, 3000);
            } else {
              chip.innerText = "Failed to generate";
            }
          }
        );
      });

      ta.parentNode?.insertBefore(chip, ta);
    }
  }

  // Inject after a short delay for SPA dynamic rendering
  setTimeout(injectFloatingBadge, 1200);
  setTimeout(injectScreenerChips, 1500);
  setInterval(injectScreenerChips, 3000);

  // Listen for trigger from popup
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === "TRIGGER_AUTOFILL") {
      chrome.runtime.sendMessage({ action: "GET_PROFILE" }, (response) => {
        if (response && response.success && response.profile) {
          const count = autofillForm(response.profile);
          sendResponse({ success: true, count });
        } else {
          sendResponse({ success: false, error: "Could not load candidate profile" });
        }
      });
      return true;
    }
  });
})();
