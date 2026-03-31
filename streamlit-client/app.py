from __future__ import annotations

import base64
import os

import streamlit as st

from api_client import api_delete, api_get, api_patch, api_post
from auth_guard import hide_dev_auth_nav, is_authenticated

BACKEND_DEFAULT = "http://127.0.0.1:8000"

st.set_page_config(page_title="clearhire.ai", page_icon="CH", layout="wide")
hide_dev_auth_nav()


def _extract_error_message(response) -> str:
    try:
        payload = response.json()
        if isinstance(payload, dict):
            detail = payload.get("detail")
            if isinstance(detail, list):
                parts: list[str] = []
                for item in detail:
                    if isinstance(item, dict):
                        parts.append(str(item.get("msg", item)))
                    else:
                        parts.append(str(item))
                return "; ".join(parts) if parts else response.text
            if detail:
                return str(detail)
        return response.text
    except Exception:
        return response.text


def _is_truthy_env(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _data_url_from_upload(uploaded_file) -> str:
    mime = uploaded_file.type or "image/png"
    encoded = base64.b64encode(uploaded_file.getvalue()).decode("utf-8")
    return f"data:{mime};base64,{encoded}"


def _data_url_to_bytes(data_url: str | None) -> bytes | None:
    if not data_url:
        return None
    try:
        _, b64_payload = data_url.split(",", 1)
        return base64.b64decode(b64_payload)
    except Exception:
        return None


def _profile_initials(user: dict) -> str:
    source = (user.get("full_name") or user.get("email") or "U").strip()
    letters = [part[0] for part in source.replace("@", " ").replace(".", " ").split() if part]
    return ("".join(letters)[:2] or "U").upper()


def _seed_profile_state(user: dict) -> None:
    user_id = user.get("id", "")
    if st.session_state.get("profile_seed_user_id") == user_id:
        return

    st.session_state.profile_seed_user_id = user_id
    st.session_state.profile_full_name = user.get("full_name") or ""
    st.session_state.profile_headline = user.get("headline") or ""
    st.session_state.profile_location = user.get("location") or ""
    st.session_state.profile_phone = user.get("phone") or ""
    st.session_state.profile_bio = user.get("bio") or ""
    st.session_state.profile_image_data_url = user.get("profile_image_data_url") or ""


st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@500;700;800&family=DM+Sans:wght@400;500;700&display=swap');

    :root {
        --bg-space: #070e1b;
        --bg-input: rgba(6, 16, 36, 0.9);
        --bg-input-metal-a: #123d78;
        --bg-input-metal-b: #0b2f64;
        --input-border: rgba(108, 182, 255, 0.64);
        --input-border-focus: #6fb5ff;
        --input-text: #ff9f2f;
        --input-placeholder: #ffc170;
        --text-main: #e7f0ff;
        --text-muted: #8ca0bf;
        --accent: #2e6ef7;
        --accent-strong: #3f88ff;
        --orb-a: rgba(46, 110, 247, 0.24);
        --orb-b: rgba(19, 163, 255, 0.16);
        --orb-c: rgba(126, 91, 255, 0.12);
    }

    @keyframes driftStars {
        0% { transform: translateY(0); }
        100% { transform: translateY(-140px); }
    }

    @keyframes pulseGlow {
        0% { opacity: 0.45; }
        50% { opacity: 0.72; }
        100% { opacity: 0.45; }
    }

    @keyframes orbitFloat {
        0% { transform: translateY(0px) translateX(0px); }
        50% { transform: translateY(-8px) translateX(4px); }
        100% { transform: translateY(0px) translateX(0px); }
    }

    @keyframes fadeUp {
        from { opacity: 0; transform: translateY(14px); }
        to { opacity: 1; transform: translateY(0); }
    }

    @keyframes earthSpin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }

    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
        color: var(--text-main);
        margin: 0;
        background: var(--bg-space) !important;
    }

    [data-testid="stApp"],
    [data-testid="stMain"],
    section.main,
    [data-testid="stMainBlockContainer"] {
        background: transparent !important;
    }

    [data-testid="stAppViewContainer"] {
        position: relative;
        min-height: 100vh;
        background:
            radial-gradient(60vw 46vw at 18% 65%, rgba(32, 77, 150, 0.24), transparent 65%),
            radial-gradient(50vw 40vw at 76% 20%, rgba(19, 98, 205, 0.22), transparent 70%),
            var(--bg-space);
        overflow: hidden;
    }

    [data-testid="stAppViewContainer"]::before {
        content: "";
        position: fixed;
        inset: -10% -10% -10% -10%;
        background-image:
            radial-gradient(1.2px 1.2px at 12% 18%, rgba(255,255,255,0.9), transparent 65%),
            radial-gradient(1.1px 1.1px at 20% 62%, rgba(255,255,255,0.85), transparent 65%),
            radial-gradient(0.9px 0.9px at 34% 42%, rgba(255,255,255,0.75), transparent 65%),
            radial-gradient(1.3px 1.3px at 58% 16%, rgba(255,255,255,0.85), transparent 65%),
            radial-gradient(1.0px 1.0px at 70% 54%, rgba(255,255,255,0.8), transparent 65%),
            radial-gradient(1.1px 1.1px at 86% 32%, rgba(255,255,255,0.8), transparent 65%),
            radial-gradient(1.0px 1.0px at 92% 70%, rgba(255,255,255,0.9), transparent 65%);
        background-size: 520px 520px;
        animation: driftStars 44s linear infinite;
        z-index: -3;
        pointer-events: none;
        opacity: 0.45;
    }

    [data-testid="stAppViewContainer"]::after {
        content: "";
        position: fixed;
        inset: -10% -10% -10% -10%;
        background-image:
            radial-gradient(0.9px 0.9px at 16% 28%, rgba(255,255,255,0.7), transparent 65%),
            radial-gradient(1.1px 1.1px at 48% 20%, rgba(255,255,255,0.72), transparent 65%),
            radial-gradient(0.9px 0.9px at 64% 74%, rgba(255,255,255,0.68), transparent 65%),
            radial-gradient(1.1px 1.1px at 78% 44%, rgba(255,255,255,0.74), transparent 65%);
        background-size: 680px 680px;
        animation: driftStars 72s linear infinite reverse;
        z-index: -2;
        pointer-events: none;
        opacity: 0.32;
    }

    .orb {
        position: fixed;
        border-radius: 50%;
        filter: blur(48px);
        pointer-events: none;
        z-index: -1;
        animation: orbitFloat 8s ease-in-out infinite;
    }

    .orb-a {
        width: 280px;
        height: 280px;
        left: 9%;
        top: 16%;
        background: var(--orb-a);
    }

    .orb-b {
        width: 220px;
        height: 220px;
        right: 16%;
        top: 56%;
        background: var(--orb-b);
        animation-delay: 1.4s;
    }

    .orb-c {
        width: 180px;
        height: 180px;
        right: 7%;
        bottom: 9%;
        background: var(--orb-c);
        animation-delay: 2.1s;
    }

    [data-testid="stHeader"] {
        background: rgba(0, 0, 0, 0);
    }

    [data-testid="stToolbar"] {
        display: none !important;
    }

    [data-testid="stStatusWidget"] {
        display: none !important;
    }

    [data-testid="stSidebarCollapsedControl"],
    [data-testid="collapsedControl"],
    #MainMenu,
    footer {
        visibility: hidden !important;
        display: none !important;
    }

    .left-panel {
        position: relative;
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
        min-height: 80vh;
        padding: 40px 20px;
        animation: fadeUp 700ms ease both;
    }

    .brand-heading {
        font-family: 'Syne', sans-serif;
        font-size: clamp(20px, 2.2vw, 32px);
        font-weight: 800;
        letter-spacing: 0.02em;
        color: #e8f1ff;
        margin: 0 0 14px;
        text-transform: lowercase;
    }

    .earth-globe {
        width: clamp(420px, 48vw, 640px);
        height: clamp(420px, 48vw, 640px);
        border-radius: 50%;
        position: absolute;
        top: 14px;
        right: -170px;
        z-index: 0;
        object-fit: cover;
        box-shadow: 0 0 60px rgba(46,110,247,0.5);
        overflow: hidden;
        animation: earthSpin 180s linear infinite;
        transform-origin: center center;
        will-change: transform;
        filter: saturate(1.08) contrast(1.06);
        pointer-events: none;
    }

    .earth-atmo {
        position: absolute;
        width: clamp(460px, 52vw, 700px);
        height: clamp(460px, 52vw, 700px);
        top: -8px;
        right: -200px;
        border-radius: 50%;
        z-index: 1;
        border: 1px solid rgba(114, 191, 255, 0.36);
        filter: blur(2px);
        animation: pulseGlow 7s ease-in-out infinite;
        pointer-events: none;
    }

    .left-copy {
        position: relative;
        z-index: 10;
        max-width: 640px;
    }

    .left-copy * {
        position: relative;
        z-index: 10;
    }

    .auth-title {
        font-family: 'Syne', sans-serif;
        font-size: clamp(28px, 3vw, 42px);
        font-weight: 800;
        line-height: 1.15;
        color: var(--text-main);
        margin-top: 64px;
        margin-bottom: 0.7rem;
        letter-spacing: -0.025em;
    }

    .auth-sub {
        font-size: 14px;
        color: var(--text-muted);
        margin: 12px 0 28px;
        max-width: 520px;
        line-height: 1.58;
    }

    .chip-row {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
    }

    .feature-chip {
        padding: 8px 16px;
        border-radius: 999px;
        border: 1px solid rgba(255,255,255,0.15);
        font-size: 13px;
        color: #c0d4f5;
        background: rgba(255,255,255,0.05);
        animation: fadeUp 850ms ease both;
    }

    /* Real login card rendered by Streamlit tabs in the right column */
    div[data-testid="stHorizontalBlock"]:first-of-type > div:nth-child(2) > div[data-testid="stVerticalBlock"] {
        min-height: 80vh;
        display: flex;
        align-items: flex-start;
        justify-content: center;
        padding-top: 40px;
    }

    div[data-testid="stHorizontalBlock"]:first-of-type > div:nth-child(2) [data-testid="stTabs"] {
        background: rgba(10, 22, 50, 0.75);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 20px;
        padding: 30px 28px 24px;
        width: 100%;
        max-width: 460px;
        box-shadow: 0 8px 40px rgba(0,0,0,0.4);
        z-index: 10;
        position: relative;
    }

    div[data-testid="stTextInput"] > label {
        display: none !important;
    }

    div[data-testid="stTextInput"] > div > div,
    div[data-testid="stTextInput"] div[data-baseweb="input"] {
        width: 100% !important;
        background:
            linear-gradient(145deg, var(--bg-input-metal-a), var(--bg-input-metal-b)) !important;
        border: 1px solid var(--input-border) !important;
        border-radius: 10px !important;
        box-shadow: inset 0 1px 1px rgba(255,255,255,0.2), inset 0 -8px 14px rgba(1, 17, 45, 0.35);
        transition: border-color 150ms ease, box-shadow 150ms ease;
    }

    div[data-testid="stTextInput"] > div > div:focus-within,
    div[data-testid="stTextInput"] div[data-baseweb="input"]:focus-within {
        border-color: var(--input-border-focus) !important;
        box-shadow: 0 0 0 2px rgba(86, 156, 255, 0.33), inset 0 1px 1px rgba(255,255,255,0.24), inset 0 -8px 14px rgba(1, 17, 45, 0.35) !important;
    }

    div[data-testid="stTextInput"] input,
    div[data-baseweb="input"] input {
        padding: 14px 16px !important;
        color: var(--input-text) !important;
        -webkit-text-fill-color: var(--input-text) !important;
        caret-color: var(--input-text) !important;
        background: transparent !important;
        font-size: 15px !important;
    }

    div[data-baseweb="input"] input::placeholder {
        color: var(--input-placeholder) !important;
        opacity: 1 !important;
    }

    div[data-baseweb="input"] input:-webkit-autofill,
    div[data-baseweb="input"] input:-webkit-autofill:hover,
    div[data-baseweb="input"] input:-webkit-autofill:focus,
    div[data-baseweb="input"] input:-webkit-autofill:active {
        -webkit-text-fill-color: var(--input-text) !important;
        caret-color: var(--input-text) !important;
        -webkit-box-shadow: 0 0 0 1000px #0f376f inset !important;
        box-shadow: 0 0 0 1000px #0f376f inset !important;
        transition: background-color 9999s ease-in-out 0s;
    }

    input[type="text"], input[type="password"], input[type="email"] {
        width: 100% !important;
        padding: 14px 16px !important;
        background: transparent !important;
        border: 1px solid var(--input-border) !important;
        border-radius: 10px !important;
        color: var(--input-text) !important;
        font-size: 15px !important;
    }

    div[data-baseweb="input"] svg {
        fill: #ffc06a !important;
    }

    div[data-testid="stFormSubmitButton"] button,
    div.stButton > button {
        border-radius: 12px !important;
        border: 1px solid rgba(129, 177, 255, 0.62) !important;
        background: linear-gradient(140deg, #245ed2, #2e6ef7) !important;
        color: #f4f8ff !important;
        font-weight: 600 !important;
        box-shadow: 0 0 0 rgba(46, 110, 247, 0);
        transition: box-shadow 180ms ease, transform 140ms ease, filter 140ms ease;
    }

    div[data-testid="stFormSubmitButton"] button:hover,
    div.stButton > button:hover {
        border-color: rgba(182, 212, 255, 0.94) !important;
        box-shadow: 0 0 20px rgba(46, 110, 247, 0.46);
        transform: translateY(-1px);
        filter: brightness(1.06);
    }

    [data-baseweb="tab"] {
        color: #c9dcff !important;
        font-weight: 500 !important;
    }

    [data-baseweb="tab-highlight"] {
        background: var(--accent) !important;
        height: 2px !important;
    }

    [data-testid="InputInstructions"] {
        display: none !important;
    }

    h1, h2, h3, h4 {
        color: #edf3ff !important;
        font-family: 'Syne', sans-serif;
    }

    p, li, span, div {
        color: #d4e1fb;
    }

    @media (max-width: 900px) {
        .left-panel {
            min-height: auto;
            padding: 16px 8px;
        }

        .earth-globe {
            width: 300px;
            height: 300px;
            top: 20px;
            right: -94px;
        }

        .earth-atmo {
            width: 330px;
            height: 330px;
            top: 2px;
            right: -108px;
        }

        .auth-title {
            margin-top: 54px;
        }

        div[data-testid="stHorizontalBlock"]:first-of-type > div:nth-child(2) > div[data-testid="stVerticalBlock"] {
            min-height: auto;
            padding-top: 16px;
            display: block;
        }

        div[data-testid="stHorizontalBlock"]:first-of-type > div:nth-child(2) [data-testid="stTabs"] {
            max-width: 100%;
            padding: 22px 18px 18px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if "api_base" not in st.session_state:
    st.session_state.api_base = BACKEND_DEFAULT

authenticated = is_authenticated()

if not authenticated:
    st.markdown('<div class="orb orb-a"></div><div class="orb orb-b"></div><div class="orb orb-c"></div>', unsafe_allow_html=True)
    st.markdown(
        """
        <style>
        [data-testid="stMainBlockContainer"] {
            max-width: 100% !important;
            padding-top: 0 !important;
            padding-bottom: 0 !important;
        }

        div[data-testid="stHorizontalBlock"]:first-of-type {
            display: grid !important;
            grid-template-columns: 1fr 1fr !important;
            min-height: 100vh;
            align-items: center;
            padding: 40px;
            gap: 60px;
        }

        @media (max-width: 900px) {
            div[data-testid="stHorizontalBlock"]:first-of-type {
                grid-template-columns: 1fr !important;
                min-height: auto;
                padding: 20px;
                gap: 24px;
            }
        }

        [data-testid="stSidebar"] { display: none !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        st.markdown(
            """
            <div class="left-panel">
                <img class="earth-globe" src="https://upload.wikimedia.org/wikipedia/commons/9/97/The_Earth_seen_from_Apollo_17.jpg" alt="Earth" />
                <div class="earth-atmo"></div>
                <div class="left-copy">
                    <div class="brand-heading">clearhire.ai</div>
                    <div class="auth-title">Craft smarter job moves with an AI-first workspace.</div>
                    <div class="auth-sub">Securely login to start resume intelligence, semantic matching, and automated top-match digests.</div>
                    <div class="chip-row">
                        <span class="feature-chip">Semantic Resume Matching</span>
                        <span class="feature-chip">Daily Scheduler</span>
                        <span class="feature-chip">Top-Match Email Digest</span>
                        <span class="feature-chip">15-Day Data Retention</span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_right:
        tab_login, tab_signup = st.tabs(["Login", "Create Account"])

        with tab_login:
            with st.form("login_form", enter_to_submit=False):
                login_email = st.text_input(
                    "Email",
                    key="home_login_email",
                    placeholder="Email",
                    label_visibility="collapsed",
                )
                login_password = st.text_input(
                    "Password",
                    type="password",
                    key="home_login_password",
                    placeholder="Password",
                    label_visibility="collapsed",
                )
                login_submitted = st.form_submit_button("Login", type="primary")

            if login_submitted:
                if not login_email.strip() or not login_password.strip():
                    st.error("Email and password are required.")
                else:
                    try:
                        response = api_post(
                            "/api/auth/login",
                            payload={"email": login_email.strip(), "password": login_password},
                        )
                        if response.status_code >= 400:
                            st.error(f"Login failed: {_extract_error_message(response)}")
                        else:
                            st.session_state.auth_token = response.json().get("access_token", "")
                            st.success("Login successful")
                            st.rerun()
                    except Exception as exc:
                        st.error(f"Login failed: {exc}")

        with tab_signup:
            with st.form("signup_form", enter_to_submit=False):
                signup_email = st.text_input(
                    "Email",
                    key="home_signup_email",
                    placeholder="Email",
                    label_visibility="collapsed",
                )
                signup_password = st.text_input(
                    "Password",
                    type="password",
                    key="home_signup_password",
                    placeholder="Create password",
                    label_visibility="collapsed",
                )
                signup_submitted = st.form_submit_button("Create Account", type="primary")

            if signup_submitted:
                if not signup_email.strip() or not signup_password.strip():
                    st.error("Email and password are required.")
                else:
                    try:
                        register_response = api_post(
                            "/api/auth/register",
                            payload={"email": signup_email.strip(), "password": signup_password},
                        )
                        if register_response.status_code >= 400:
                            st.error(f"Create account failed: {_extract_error_message(register_response)}")
                        else:
                            login_response = api_post(
                                "/api/auth/login",
                                payload={"email": signup_email.strip(), "password": signup_password},
                            )
                            if login_response.status_code >= 400:
                                st.success("Account created. Please login from the Login tab.")
                            else:
                                st.session_state.auth_token = login_response.json().get("access_token", "")
                                st.success("Account created. You are now logged in.")
                                st.rerun()
                    except Exception as exc:
                        st.error(f"Create account failed: {exc}")

    st.stop()

st.markdown(
    """
    <style>
    .dash-card {
        background: linear-gradient(155deg, rgba(15, 43, 90, 0.58), rgba(7, 21, 48, 0.52));
        border: 1px solid rgba(128, 184, 255, 0.26);
        border-radius: 18px;
        padding: 18px 18px 14px;
        box-shadow: 0 14px 32px rgba(0, 0, 0, 0.24);
    }

    .dash-metric {
        background: linear-gradient(150deg, rgba(20, 54, 108, 0.68), rgba(8, 28, 66, 0.64));
        border: 1px solid rgba(124, 176, 255, 0.3);
        border-radius: 14px;
        padding: 12px;
        text-align: center;
        color: #dce9ff;
    }

    .profile-menu-name {
        margin: 8px 0 2px;
        color: #edf3ff;
        font-weight: 700;
        font-size: 18px;
        line-height: 1.2;
    }

    .profile-menu-email {
        margin: 0 0 12px;
        color: #b8ccea;
        font-size: 12px;
        word-break: break-all;
    }

    .profile-menu-list-title {
        margin: 8px 0 6px;
        color: #dceaff;
        font-weight: 600;
    }

    .profile-menu-note {
        margin: 8px 0 0;
        color: #a8c2e9;
        font-size: 12px;
    }

    .avatar-fallback {
        width: 88px;
        height: 88px;
        border-radius: 999px;
        background: linear-gradient(155deg, rgba(34, 96, 188, 0.95), rgba(14, 45, 97, 0.95));
        border: 1px solid rgba(168, 208, 255, 0.56);
        color: #f4f9ff;
        display: flex;
        align-items: center;
        justify-content: center;
        font-family: 'Syne', sans-serif;
        font-size: 30px;
        font-weight: 700;
    }

    .avatar-fallback.avatar-small {
        width: 68px;
        height: 68px;
        font-size: 24px;
        margin: 2px auto 6px;
    }

    .profile-danger-note {
        color: #f2b49d;
        font-size: 12px;
        line-height: 1.4;
        margin: 8px 0 2px;
    }

    div[data-testid="stPopover"] {
        display: flex;
        justify-content: flex-end;
    }

    div[data-testid="stPopover"] button {
        min-width: 48px;
        height: 48px;
        border-radius: 999px !important;
        font-family: 'Syne', sans-serif;
        font-size: 18px !important;
        border: 1px solid rgba(146, 200, 255, 0.7) !important;
        background: linear-gradient(150deg, rgba(33, 95, 184, 0.95), rgba(14, 45, 97, 0.95)) !important;
        color: #f4f9ff !important;
        box-shadow: 0 6px 16px rgba(8, 29, 72, 0.4);
    }

    div[data-testid="stPopover"] button:hover {
        transform: translateY(-1px);
        filter: brightness(1.08);
    }

    div[data-testid="stPopoverContent"],
    div[data-baseweb="popover"] > div {
        background: linear-gradient(160deg, rgba(16, 48, 99, 0.96), rgba(8, 28, 66, 0.98));
        border: 1px solid rgba(138, 192, 255, 0.38);
        border-radius: 16px;
        box-shadow: 0 20px 38px rgba(5, 20, 52, 0.48);
    }

    div[data-testid="stPopoverContent"] p,
    div[data-testid="stPopoverContent"] li,
    div[data-testid="stPopoverContent"] label,
    div[data-baseweb="popover"] p,
    div[data-baseweb="popover"] li,
    div[data-baseweb="popover"] label {
        color: #dce9ff !important;
    }

    div[data-testid="stPopoverContent"] div[data-testid="stForm"],
    div[data-baseweb="popover"] div[data-testid="stForm"] {
        border: 1px solid rgba(133, 185, 255, 0.26);
        border-radius: 12px;
        padding: 10px 10px 2px;
        background: linear-gradient(155deg, rgba(12, 37, 80, 0.52), rgba(9, 29, 65, 0.52));
    }

    div[data-testid="stPopoverContent"] div[data-testid="stForm"] label p,
    div[data-testid="stPopoverContent"] div[data-testid="stTextInput"] label p,
    div[data-testid="stPopoverContent"] div[data-testid="stTextArea"] label p,
    div[data-testid="stPopoverContent"] div[data-testid="stFileUploader"] label,
    div[data-baseweb="popover"] div[data-testid="stForm"] label p,
    div[data-baseweb="popover"] div[data-testid="stTextInput"] label p,
    div[data-baseweb="popover"] div[data-testid="stTextArea"] label p,
    div[data-baseweb="popover"] div[data-testid="stFileUploader"] label {
        color: #bcd4f3 !important;
        font-size: 12px !important;
        font-weight: 600 !important;
    }

    div[data-testid="stPopoverContent"] div[data-baseweb="input"],
    div[data-baseweb="popover"] div[data-baseweb="input"] {
        background: rgba(8, 27, 58, 0.92) !important;
        border: 1px solid rgba(108, 164, 236, 0.48) !important;
        border-radius: 10px !important;
    }

    div[data-testid="stPopoverContent"] div[data-baseweb="input"] input,
    div[data-baseweb="popover"] div[data-baseweb="input"] input {
        color: #e9f2ff !important;
        -webkit-text-fill-color: #e9f2ff !important;
        caret-color: #e9f2ff !important;
        background: transparent !important;
    }

    div[data-testid="stPopoverContent"] div[data-baseweb="input"] input::placeholder,
    div[data-baseweb="popover"] div[data-baseweb="input"] input::placeholder {
        color: #97b6df !important;
    }

    div[data-testid="stPopoverContent"] div[data-testid="stTextArea"] textarea,
    div[data-baseweb="popover"] div[data-testid="stTextArea"] textarea {
        background: rgba(8, 27, 58, 0.92) !important;
        color: #e9f2ff !important;
        border: 1px solid rgba(108, 164, 236, 0.48) !important;
        border-radius: 10px !important;
    }

    div[data-testid="stPopoverContent"] div[data-testid="stFileUploaderDropzone"],
    div[data-baseweb="popover"] div[data-testid="stFileUploaderDropzone"] {
        background: rgba(9, 31, 71, 0.7);
        border: 1px dashed rgba(118, 180, 255, 0.44);
        border-radius: 12px;
    }

    div[data-testid="stPopoverContent"] div.stButton > button,
    div[data-baseweb="popover"] div.stButton > button {
        width: 100%;
    }

    div[data-testid="stPopoverContent"] div.stButton > button[kind="secondary"],
    div[data-testid="stPopoverContent"] div[data-testid="stFormSubmitButton"] button[kind="secondary"],
    div[data-baseweb="popover"] div.stButton > button[kind="secondary"],
    div[data-baseweb="popover"] div[data-testid="stFormSubmitButton"] button[kind="secondary"] {
        background: linear-gradient(140deg, #8c2a28, #c73f3d) !important;
        border: 1px solid rgba(255, 177, 170, 0.62) !important;
        color: #fff1ee !important;
    }

    .auth-hero-cue {
        margin-top: 18px;
        color: #a9c8ff;
        font-size: 14px;
        letter-spacing: 0.01em;
        display: inline-flex;
        align-items: center;
        gap: 10px;
        opacity: 0.95;
    }

    .auth-hero-cue .arrow {
        display: inline-block;
        animation: cueBounce 1.8s ease-in-out infinite;
        color: #ffaf4c;
        font-weight: 700;
    }

    .page-break-spacer {
        height: clamp(120px, 18vh, 240px);
    }

    .feature-section {
        min-height: 100vh;
        padding: clamp(18px, 4vh, 36px) 0 42px;
    }

    .feature-section h2 {
        font-family: 'Syne', sans-serif;
        font-size: clamp(28px, 3.2vw, 40px);
        margin-bottom: 8px;
        color: #edf3ff;
    }

    .feature-section .feature-lead {
        margin: 0 0 18px;
        max-width: 740px;
        color: #aac1e8;
        font-size: 15px;
        line-height: 1.6;
    }

    .feature-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 14px;
        margin-top: 12px;
    }

    .feature-card {
        background: linear-gradient(155deg, rgba(23, 67, 133, 0.58), rgba(10, 35, 79, 0.66));
        border: 1px solid rgba(124, 186, 255, 0.34);
        border-radius: 16px;
        padding: 16px 16px 14px;
        backdrop-filter: blur(8px);
        box-shadow: 0 12px 26px rgba(4, 16, 40, 0.34);
        min-height: 190px;
    }

    .feature-tag {
        display: inline-block;
        border: 1px solid rgba(255, 178, 84, 0.6);
        border-radius: 999px;
        font-size: 11px;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        color: #ffbd66;
        padding: 4px 9px;
        margin-bottom: 10px;
    }

    .feature-card h3 {
        margin: 0 0 8px;
        font-family: 'Syne', sans-serif;
        font-size: 21px;
        line-height: 1.2;
        color: #f2f6ff;
    }

    .feature-card p {
        margin: 0;
        font-size: 14px;
        line-height: 1.55;
        color: #b7cdee;
    }

    @keyframes cueBounce {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(4px); }
    }

    @media (max-width: 900px) {
        .page-break-spacer {
            height: 72px;
        }

        .feature-card {
            min-height: 168px;
        }

        div[data-testid="stPopover"] button {
            min-width: 44px;
            height: 44px;
            font-size: 16px !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

user = st.session_state.get("current_user", {})
_seed_profile_state(user)
show_dev_tools = _is_truthy_env("SHOW_DEV_TOOLS")

top_nav_left, top_nav_right = st.columns([9, 1], gap="small")
with top_nav_right:
    profile_menu = st.popover(_profile_initials(user), help="Profile menu")

with profile_menu:
    avatar_bytes = _data_url_to_bytes(st.session_state.get("profile_image_data_url") or user.get("profile_image_data_url"))
    if avatar_bytes:
        st.image(avatar_bytes, width=68)
    else:
        st.markdown(f'<div class="avatar-fallback avatar-small">{_profile_initials(user)}</div>', unsafe_allow_html=True)

    display_name = (st.session_state.get("profile_full_name") or "").strip()
    if not display_name:
        email = user.get("email", "")
        display_name = email.split("@")[0] if email else "User"

    st.markdown(f'<p class="profile-menu-name">{display_name}</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="profile-menu-email">{user.get("email", "")}</p>', unsafe_allow_html=True)

    st.markdown('<p class="profile-menu-list-title">Profile Menu</p>', unsafe_allow_html=True)
    st.markdown(
        """
        - Personal details
        - Upload profile picture
        - Logout
        - Delete account
        """
    )

    with st.expander("Edit Personal Details", expanded=False):
        with st.form("profile_form"):
            st.text_input("Full Name", key="profile_full_name")
            st.text_input("Phone", key="profile_phone")
            st.text_input("Headline", key="profile_headline")
            st.text_input("Location", key="profile_location")
            st.text_area("About", key="profile_bio", height=84)
            uploaded_avatar = st.file_uploader(
                "Upload Profile Picture",
                type=["png", "jpg", "jpeg", "webp"],
                key="profile_photo_upload",
            )
            clear_avatar = st.checkbox("Remove photo", value=False, key="profile_clear_photo")
            save_profile = st.form_submit_button("Save Profile", type="primary", use_container_width=True)

        if save_profile:
            payload = {
                "full_name": st.session_state.get("profile_full_name", ""),
                "headline": st.session_state.get("profile_headline", ""),
                "location": st.session_state.get("profile_location", ""),
                "phone": st.session_state.get("profile_phone", ""),
                "bio": st.session_state.get("profile_bio", ""),
            }
            if clear_avatar:
                payload["clear_profile_image"] = True
            elif uploaded_avatar is not None:
                payload["profile_image_data_url"] = _data_url_from_upload(uploaded_avatar)

            try:
                response = api_patch("/api/auth/me", payload=payload)
                if response.status_code >= 400:
                    st.error(f"Profile update failed: {_extract_error_message(response)}")
                else:
                    updated_user = response.json()
                    st.session_state.current_user = updated_user
                    st.session_state.profile_image_data_url = updated_user.get("profile_image_data_url") or ""
                    st.session_state.profile_clear_photo = False
                    st.success("Profile updated")
                    st.rerun()
            except Exception as exc:
                st.error(f"Profile update failed: {exc}")

    with st.expander("Account Actions", expanded=False):
        delete_confirm = st.text_input(
            "Type DELETE to confirm account deletion",
            key="delete_confirm_phrase",
        )
        if st.button("Logout", key="profile_logout_button", use_container_width=True):
            st.session_state.auth_token = ""
            st.session_state.current_user = {}
            st.rerun()

        if st.button("Delete Account", key="profile_delete_button", type="secondary", use_container_width=True):
            if delete_confirm.strip() != "DELETE":
                st.warning("Type DELETE in the confirmation field first.")
            else:
                try:
                    response = api_delete("/api/auth/account", params={"confirm": "DELETE"})
                    if response.status_code >= 400:
                        st.error(f"Delete account failed: {_extract_error_message(response)}")
                    else:
                        st.session_state.auth_token = ""
                        st.session_state.current_user = {}
                        for key in list(st.session_state.keys()):
                            if key.startswith("profile_"):
                                del st.session_state[key]
                        st.success("Account deleted")
                        st.rerun()
                except Exception as exc:
                    st.error(f"Delete account failed: {exc}")

        st.markdown('<p class="profile-danger-note">Deleting the account removes your profile and owned resume records from this workspace.</p>', unsafe_allow_html=True)

    if show_dev_tools:
        with st.expander("Developer Diagnostics", expanded=False):
            if st.button("Check Backend Health", key="dev_check_health"):
                try:
                    response = api_get("/health")
                    response.raise_for_status()
                    st.success("Backend reachable")
                    st.json(response.json())
                except Exception as exc:
                    st.error(f"Health check failed: {exc}")

    st.markdown('<p class="profile-menu-note">Click outside this menu to close it.</p>', unsafe_allow_html=True)

st.title("clearhire.ai")
st.caption("Authenticated workspace for resume intelligence, job matching, and digest automation")

st.markdown('<div class="dash-card">', unsafe_allow_html=True)
st.subheader("Welcome")
if user:
    st.write(f"Logged in as: {user.get('email', 'user')}")
st.write("Run flow in this order:")
st.write("1. Upload Resume")
st.write("2. Match JD")
st.write("3. Tailor Resume")
st.write("4. Job Preferences (scheduler + email)")
st.write("5. Scrape and digest")
st.markdown('</div>', unsafe_allow_html=True)

stats1, stats2, stats3 = st.columns(3)
with stats1:
    st.markdown('<div class="dash-metric"><b>Auth</b><br/>Required</div>', unsafe_allow_html=True)
with stats2:
    st.markdown('<div class="dash-metric"><b>Retention</b><br/>15 days</div>', unsafe_allow_html=True)
with stats3:
    st.markdown('<div class="dash-metric"><b>Scheduler</b><br/>Daily 09:00 default</div>', unsafe_allow_html=True)

st.markdown('<div class="auth-hero-cue">Scroll down for feature workspace <span class="arrow">&#8595;</span></div>', unsafe_allow_html=True)
st.markdown('<div class="page-break-spacer"></div>', unsafe_allow_html=True)

st.markdown(
    """
    <section class="feature-section">
        <h2>Feature Workspace</h2>
        <p class="feature-lead">All modules are tuned for responsive use so you can continue your full resume-to-application workflow from desktop and mobile without layout breaks.</p>
        <div class="feature-grid">
            <article class="feature-card">
                <span class="feature-tag">Resume</span>
                <h3>Upload Resume</h3>
                <p>Upload PDF or DOCX with extension, MIME, and signature checks before parsing to keep files safe and valid.</p>
            </article>
            <article class="feature-card">
                <span class="feature-tag">Matching</span>
                <h3>Match Job Description</h3>
                <p>Compare your resume with job descriptions using keyword overlap and embedding-based semantic scoring.</p>
            </article>
            <article class="feature-card">
                <span class="feature-tag">Tailoring</span>
                <h3>Tailor Resume</h3>
                <p>Generate role-focused resume versions with versioning support so you can target each opening quickly.</p>
            </article>
            <article class="feature-card">
                <span class="feature-tag">Tracking</span>
                <h3>Application Tracker</h3>
                <p>Manage status updates, interview progress, and application records from a single structured timeline.</p>
            </article>
            <article class="feature-card">
                <span class="feature-tag">Automation</span>
                <h3>Job Preferences</h3>
                <p>Set role, location, keywords, and scheduler time so the platform sends digest results when you want.</p>
            </article>
            <article class="feature-card">
                <span class="feature-tag">Digest</span>
                <h3>Scrape and Email Digest</h3>
                <p>Trigger job scraping and receive ranked top-match opportunities directly in your configured email digest.</p>
            </article>
        </div>
    </section>
    """,
    unsafe_allow_html=True,
)

st.subheader("Open Feature Pages")
quick_links = [
    ("pages/1_Upload_Resume.py", "Upload Resume"),
    ("pages/2_Match_JD.py", "Match JD"),
    ("pages/3_Tailor_Resume.py", "Tailor Resume"),
    ("pages/4_Applications.py", "Applications"),
    ("pages/6_Job_Preferences.py", "Job Preferences"),
    ("pages/7_Job_Scrape_and_Digest.py", "Scrape and Digest"),
]

for start in range(0, len(quick_links), 3):
    row = quick_links[start:start + 3]
    columns = st.columns(len(row))
    for column, (page_path, label) in zip(columns, row):
        with column:
            st.page_link(page_path, label=label)

st.caption("Security note: backend validates file extension, MIME, and content signature before parsing uploads.")
