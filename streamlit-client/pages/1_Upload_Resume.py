from __future__ import annotations

import streamlit as st

from auth_guard import hide_dev_auth_nav, require_login
from api_client import api_upload

hide_dev_auth_nav()
st.title("Upload Resume")
st.write("Upload PDF or DOCX. Harmful/disguised files are blocked by backend validation.")
require_login()

if "resume_id" not in st.session_state:
    st.session_state.resume_id = ""

uploaded = st.file_uploader("Select PDF or DOCX", type=["pdf", "docx"])

if st.button("Upload", type="primary"):
    if not uploaded:
        st.warning("Please select a file first.")
    else:
        try:
            response = api_upload(
                "/api/resumes/upload",
                filename=uploaded.name,
                content=uploaded.getvalue(),
                mime=uploaded.type or "application/octet-stream",
            )
            response.raise_for_status()
            data = response.json()
            st.session_state.resume_id = data["resume_id"]
            st.success(f"Uploaded successfully. Resume ID: {data['resume_id']}")
            st.json(data)
        except Exception as exc:
            st.error(f"Upload failed: {exc}")
