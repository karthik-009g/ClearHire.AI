from __future__ import annotations

import streamlit as st

from auth_guard import hide_dev_auth_nav, require_login
from api_client import api_post
from ui_theme import apply_page_theme, panel_end, panel_start

hide_dev_auth_nav()
require_login()
apply_page_theme(
    "Match Job Description",
    "Run keyword plus semantic matching against your latest resume context for a grounded fit score.",
)

panel_start()

resume_id = st.text_input("Resume ID", value=st.session_state.get("resume_id", ""))
jd_text = st.text_area("Job Description", height=220)
role = st.text_input("Role", value="Backend Engineer")
company = st.text_input("Company", value="Acme")

if st.button("Run Match"):
    payload = {
        "resume_id": resume_id,
        "jd_text": jd_text,
        "title": role,
        "company": company,
        "source": "streamlit-client",
    }
    try:
        response = api_post("/api/resumes/match", payload=payload)
        response.raise_for_status()
        data = response.json()
        st.session_state.latest_match = data
        st.success("Match completed")
        st.json(data)
    except Exception as exc:
        st.error(f"Match failed: {exc}")

panel_end()
