from __future__ import annotations

import streamlit as st

from auth_guard import hide_dev_auth_nav, require_login
from api_client import api_post

hide_dev_auth_nav()
st.title("Scrape Jobs and Send Digest")
st.write("Sources include India portals and company careers pages.")
require_login()

sources = st.multiselect(
    "Sources",
    [
        "naukri",
        "linkedin",
        "accenture",
        "tcs",
        "cognizant",
        "deloitte",
        "swiggy",
        "microsoft",
        "google",
        "ibm",
    ],
    default=["naukri", "linkedin", "accenture", "tcs", "cognizant"],
)
keywords = st.text_input("Filter Keywords (comma separated)", value="python, backend, developer")
resume_id_for_matching = st.text_input("Resume ID for embedding match", value=st.session_state.get("resume_id", ""))
send_email_after_scrape = st.checkbox("Send email after scrape", value=False)

if st.button("Run Scrape"):
    payload = {
        "sources": sources,
        "keywords": [x.strip() for x in keywords.split(",") if x.strip()],
        "resume_id": resume_id_for_matching or None,
        "send_email": send_email_after_scrape,
    }
    try:
        response = api_post("/api/jobs/scrape", payload=payload)
        response.raise_for_status()
        data = response.json()
        st.success(f"Scraped jobs: {data['scraped_count']}")
        if data.get("mail_sent_to"):
            st.info(f"Digest email sent to: {data['mail_sent_to']}")
        top_matches = data.get("top_matches", [])
        if top_matches:
            st.subheader("Top Embedding Matches")
            st.json(top_matches)
        st.json(data)
    except Exception as exc:
        st.error(f"Scrape failed: {exc}")

st.markdown("---")
st.subheader("Email Matched Jobs Digest")
resume_id = st.text_input("Resume ID for matching")
email_override = st.text_input("Email Override (optional)")

if st.button("Send Digest Email", type="primary"):
    payload = {
        "resume_id": resume_id,
        "preferred_email": email_override or None,
        "sources": sources,
    }
    try:
        response = api_post("/api/jobs/digest", payload=payload)
        response.raise_for_status()
        st.success("Digest sent")
        st.json(response.json())
    except Exception as exc:
        st.error(f"Digest failed: {exc}")
