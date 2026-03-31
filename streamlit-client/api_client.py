from __future__ import annotations

import requests
import streamlit as st


def get_api_base() -> str:
    return st.session_state.get("api_base", "http://127.0.0.1:8000").rstrip("/")


def get_headers() -> dict[str, str]:
    token = st.session_state.get("auth_token", "")
    headers: dict[str, str] = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def api_get(path: str, timeout: int = 30):
    return requests.get(f"{get_api_base()}{path}", headers=get_headers(), timeout=timeout)


def api_post(path: str, payload: dict | None = None, timeout: int = 60):
    return requests.post(f"{get_api_base()}{path}", json=payload, headers=get_headers(), timeout=timeout)


def api_post_raw(path: str, payload: dict | None = None, timeout: int = 60):
    return requests.post(f"{get_api_base()}{path}", json=payload, headers=get_headers(), timeout=timeout)


def api_patch(path: str, payload: dict | None = None, timeout: int = 60):
    return requests.patch(f"{get_api_base()}{path}", json=payload, headers=get_headers(), timeout=timeout)


def api_delete(path: str, params: dict | None = None, timeout: int = 60):
    return requests.delete(f"{get_api_base()}{path}", params=params, headers=get_headers(), timeout=timeout)


def api_upload(path: str, filename: str, content: bytes, mime: str, timeout: int = 60):
    files = {"file": (filename, content, mime)}
    return requests.post(f"{get_api_base()}{path}", files=files, headers=get_headers(), timeout=timeout)
