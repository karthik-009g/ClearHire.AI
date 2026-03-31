from __future__ import annotations

import streamlit as st

from auth_guard import hide_dev_auth_nav

hide_dev_auth_nav()
st.title("Account Access Moved")
st.info("Login and signup now happen on Home with a reactive dark auth wall.")

if st.button("Go to Home Login", type="primary"):
    try:
        st.switch_page("app.py")
    except Exception:
        st.warning("Open Home page from sidebar.")
