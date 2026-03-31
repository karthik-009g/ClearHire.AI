from __future__ import annotations

import streamlit as st

from auth_guard import hide_dev_auth_nav, require_login
from api_client import api_get, api_post, api_post_raw

hide_dev_auth_nav()
st.title("Tailor Resume")
st.info("Tailoring is copy-safe: source version is never overwritten. A new version is created.")
require_login()

resume_id = st.text_input("Resume ID", value=st.session_state.get("resume_id", ""))

source_version_no = st.number_input("Source Version Number", min_value=1, value=1, step=1)
if st.button("Load Versions"):
    if not resume_id:
        st.warning("Provide Resume ID first")
    else:
        try:
            response = api_get(f"/api/resumes/{resume_id}/versions")
            response.raise_for_status()
            data = response.json()
            st.json(data)
        except Exception as exc:
            st.error(f"Could not fetch versions: {exc}")

jd_text = st.text_area("Job Description", height=220)
role = st.text_input("Target Role", value="Backend Engineer")
company = st.text_input("Target Company", value="Acme")
candidate_name = st.text_input("Candidate Name", value="Candidate")
include_cover_letter = st.checkbox("Include Cover Letter", value=True)

if st.button("Generate Tailored Copy", type="primary"):
    payload = {
        "resume_id": resume_id,
        "source_version_no": int(source_version_no),
        "jd_text": jd_text,
        "role": role,
        "company": company,
        "source": "streamlit-client",
        "candidate_name": candidate_name,
        "include_cover_letter": include_cover_letter,
    }
    try:
        response = api_post("/api/resumes/tailor", payload=payload)
        response.raise_for_status()
        data = response.json()
        st.success(
            f"Created version {data['version_no']} from source version {data['based_on_version']}"
        )
        st.json(data)
        st.download_button(
            "Download Tailored Resume",
            data["tailored_resume_text"],
            file_name=f"tailored_resume_v{data['version_no']}.txt",
            mime="text/plain",
        )
        if data.get("cover_letter_text"):
            st.download_button(
                "Download Cover Letter",
                data["cover_letter_text"],
                file_name="cover_letter.txt",
                mime="text/plain",
            )
    except Exception as exc:
        st.error(f"Tailor failed: {exc}")

if st.button("Generate Apply-Ready ZIP"):
    payload = {
        "resume_id": resume_id,
        "source_version_no": int(source_version_no),
        "jd_text": jd_text,
        "role": role,
        "company": company,
        "source": "streamlit-client",
        "candidate_name": candidate_name,
        "include_cover_letter": include_cover_letter,
    }
    try:
        response = api_post_raw("/api/resumes/package/tailor", payload=payload)
        response.raise_for_status()
        content_disposition = response.headers.get("content-disposition", "")
        default_name = "apply_ready_package.zip"
        if "filename=" in content_disposition:
            default_name = content_disposition.split("filename=")[-1].strip('"')

        st.download_button(
            "Download Apply-Ready ZIP",
            data=response.content,
            file_name=default_name,
            mime="application/zip",
        )
        st.success("Apply-ready package generated")
    except Exception as exc:
        st.error(f"Package generation failed: {exc}")
