from __future__ import annotations

import streamlit as st

from auth_guard import hide_dev_auth_nav, require_login
from api_client import api_get, api_patch, api_post

hide_dev_auth_nav()
st.title("Applications")
require_login()
st.info("Autofill is currently on hold. Current V1 flow focuses on scrape + top-match email.")

st.subheader("Create Application Record")
job_description_id = st.number_input("Job Description ID", min_value=1, value=1, step=1)
resume_version_id = st.number_input("Resume Version ID", min_value=1, value=1, step=1)
status = st.selectbox("Status", ["pending", "applied"])
notes = st.text_input("Notes", value="")

if st.button("Create Application"):
    payload = {
        "job_description_id": int(job_description_id),
        "resume_version_id": int(resume_version_id),
        "status": status,
        "application_url": "",
        "autofill_payload": None,
        "notes": notes,
    }
    try:
        response = api_post("/api/applications/", payload=payload)
        response.raise_for_status()
        st.success("Application created")
        st.json(response.json())
    except Exception as exc:
        st.error(f"Create failed: {exc}")

st.subheader("Update Status")
app_id = st.number_input("Application ID", min_value=1, value=1, step=1, key="app_id_update")
new_status = st.selectbox("New Status", ["pending", "applied"], key="new_status")
new_notes = st.text_input("New Notes", value="", key="new_notes")
if st.button("Update Application"):
    payload = {"status": new_status, "notes": new_notes}
    try:
        response = api_patch(f"/api/applications/{int(app_id)}/status", payload=payload)
        response.raise_for_status()
        st.success("Application updated")
        st.json(response.json())
    except Exception as exc:
        st.error(f"Update failed: {exc}")

st.subheader("List Applications")
if st.button("Refresh List"):
    try:
        response = api_get("/api/applications/")
        response.raise_for_status()
        data = response.json()
        st.write(f"Total: {len(data)}")
        st.json(data)
    except Exception as exc:
        st.error(f"List failed: {exc}")
