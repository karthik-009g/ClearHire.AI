from __future__ import annotations

import streamlit as st

from auth_guard import hide_dev_auth_nav, require_login
from api_client import api_post

hide_dev_auth_nav()
st.title("Match JD")
require_login()

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
