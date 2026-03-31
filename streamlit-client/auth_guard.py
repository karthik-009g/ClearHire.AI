from __future__ import annotations

import os

import streamlit as st

from api_client import api_get


def hide_dev_auth_nav() -> None:
    show_dev_auth_page = os.getenv("SHOW_DEV_AUTH_PAGE", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    hide_auth_css = ""
    if not show_dev_auth_page:
        hide_auth_css = """
        section[data-testid=\"stSidebar\"] [data-testid=\"stSidebarNav\"] li:nth-child(6),
        section[data-testid=\"stSidebar\"] [data-testid=\"stSidebarNav\"] a[href*=\"5_Auth\"],
        section[data-testid=\"stSidebar\"] [data-testid=\"stSidebarNav\"] a[href*=\"5_Auth.py\"],
        section[data-testid=\"stSidebar\"] [data-testid=\"stSidebarNav\"] [data-testid=\"stSidebarNavLink\"][href*=\"5_Auth\"],
        section[data-testid=\"stSidebar\"] [data-testid=\"stSidebarNav\"] li:has(a[href*=\"5_Auth\"]),
        section[data-testid=\"stSidebar\"] [data-testid=\"stSidebarNav\"] li:has(a[href*=\"Auth\"]) {
            display: none !important;
        }
        """

    st.markdown(
        """
        <style>
        section[data-testid="stSidebar"] {
            background:
                radial-gradient(120% 80% at 10% 0%, rgba(65, 130, 235, 0.28), transparent 55%),
                linear-gradient(180deg, #0b1f45 0%, #08162f 100%) !important;
            border-right: 1px solid rgba(112, 168, 255, 0.22);
        }

        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] {
            padding-top: 0.45rem;
        }

        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a,
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] [data-testid="stSidebarNavLink"] {
            border-radius: 12px !important;
            margin: 2px 4px !important;
            padding: 8px 10px !important;
            color: #d7e8ff !important;
            border: 1px solid transparent;
            transition: transform 180ms ease, background-color 200ms ease, border-color 200ms ease, box-shadow 200ms ease;
            transform-origin: left center;
        }

        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a:hover,
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] [data-testid="stSidebarNavLink"]:hover {
            color: #ffffff !important;
            border-color: rgba(130, 186, 255, 0.52);
            background: linear-gradient(135deg, rgba(44, 117, 233, 0.58), rgba(19, 60, 129, 0.58)) !important;
            box-shadow: 0 10px 20px rgba(10, 40, 88, 0.4);
            transform: perspective(720px) rotateY(5deg) translateX(5px);
        }

        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"],
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] [data-testid="stSidebarNavLink"][aria-current="page"] {
            color: #ffffff !important;
            border-color: rgba(156, 204, 255, 0.72);
            background: linear-gradient(135deg, rgba(62, 136, 255, 0.72), rgba(24, 77, 164, 0.78)) !important;
            box-shadow: 0 9px 18px rgba(14, 49, 99, 0.42);
        }

        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] p {
            color: #d7e8ff !important;
            font-weight: 500;
        }
        """
        + hide_auth_css
        + """
        @media (max-width: 900px) {
            section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a:hover,
            section[data-testid="stSidebar"] [data-testid="stSidebarNav"] [data-testid="stSidebarNavLink"]:hover {
                transform: none;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def is_authenticated() -> bool:
    token = st.session_state.get("auth_token", "")
    if not token:
        return False

    try:
        response = api_get("/api/auth/me", timeout=20)
        if response.status_code >= 400:
            st.session_state.auth_token = ""
            return False
        st.session_state.current_user = response.json()
        return True
    except Exception:
        return False


def require_login() -> None:
    if not is_authenticated():
        st.warning("Please login from Home before using this page.")
        if st.button("Go to Home Login"):
            try:
                st.switch_page("app.py")
            except Exception:
                pass
        st.stop()
