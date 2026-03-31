from __future__ import annotations

import streamlit as st

from auth_guard import hide_dev_auth_nav, require_login
from api_client import api_get, api_post

hide_dev_auth_nav()
st.title("Job Preferences")
st.write("Configure email and keywords for matched jobs digest.")
st.caption("Default scheduler is once daily at 09:00 Asia/Kolkata. You can change this manually.")
require_login()

preferred_email = st.text_input("Preferred Email")
target_role = st.text_input("Target Role", value="Software Engineer")
locations = st.text_input("Locations (comma separated)", value="Bangalore, Hyderabad, Pune")
keywords = st.text_input("Keywords (comma separated)", value="python, fastapi, backend")
selected_sources = st.multiselect(
    "Sources for scrape",
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
auto_schedule_enabled = st.checkbox("Enable auto scheduler (once daily)", value=False)
schedule_time = st.text_input("Daily schedule time (HH:MM)", value="09:00")
schedule_timezone = st.text_input("Timezone", value="Asia/Kolkata")
auto_scrape_on_login = st.checkbox("Auto scrape on login", value=True)
auto_email_after_scrape = st.checkbox("Auto email after scrape", value=True)

if st.button("Save Preferences", type="primary"):
    payload = {
        "preferred_email": preferred_email,
        "target_role": target_role,
        "locations": [x.strip() for x in locations.split(",") if x.strip()],
        "keywords": [x.strip() for x in keywords.split(",") if x.strip()],
        "selected_sources": selected_sources,
        "auto_schedule_enabled": auto_schedule_enabled,
        "schedule_time": schedule_time,
        "schedule_timezone": schedule_timezone,
        "auto_scrape_on_login": auto_scrape_on_login,
        "auto_email_after_scrape": auto_email_after_scrape,
    }
    try:
        response = api_post("/api/jobs/preferences", payload=payload)
        response.raise_for_status()
        st.success("Preferences saved")
        st.json(response.json())
    except Exception as exc:
        st.error(f"Could not save preferences: {exc}")

if st.button("Load Preferences"):
    try:
        response = api_get("/api/jobs/preferences")
        response.raise_for_status()
        st.json(response.json())
    except Exception as exc:
        st.error(f"Could not load preferences: {exc}")
