from __future__ import annotations

from html import escape

import streamlit as st


def apply_page_theme(title: str, subtitle: str | None = None) -> None:
    """Apply a consistent responsive theme for authenticated Streamlit pages."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@500;600;700;800&family=Sora:wght@600;700&display=swap');

        :root {
            --ch-bg-a: #081325;
            --ch-bg-b: #102447;
            --ch-bg-c: #0d1f3d;
            --ch-card-a: rgba(17, 45, 92, 0.84);
            --ch-card-b: rgba(10, 30, 66, 0.82);
            --ch-line: rgba(143, 196, 255, 0.34);
            --ch-line-strong: rgba(183, 219, 255, 0.58);
            --ch-text: #eaf3ff;
            --ch-muted: #aac3e9;
            --ch-accent: #3d8dff;
            --ch-accent-strong: #56a3ff;
            --ch-warn: #ffc26c;
        }

        html, body, [class*="css"] {
            font-family: 'Manrope', sans-serif;
            color: var(--ch-text);
            background: var(--ch-bg-a) !important;
        }

        [data-testid="stAppViewContainer"] {
            background:
                radial-gradient(50vw 40vw at 12% 10%, rgba(82, 153, 255, 0.16), transparent 62%),
                radial-gradient(46vw 36vw at 88% 18%, rgba(56, 115, 227, 0.2), transparent 65%),
                linear-gradient(165deg, var(--ch-bg-a), var(--ch-bg-b) 45%, var(--ch-bg-c));
            overflow-x: hidden;
            overflow-y: auto;
        }

        [data-testid="stMainBlockContainer"] {
            max-width: min(1180px, 100%) !important;
            padding-top: clamp(0.8rem, 1.9vh, 1.35rem) !important;
            padding-bottom: clamp(2rem, 5.2vh, 4.2rem) !important;
        }

        [data-testid="stHeader"] {
            height: 0 !important;
            background: transparent !important;
        }

        .ch-page-head {
            margin: 2px 0 14px;
            padding: 18px 18px 16px;
            border-radius: 18px;
            border: 1px solid var(--ch-line);
            background: linear-gradient(150deg, rgba(25, 67, 135, 0.46), rgba(10, 31, 68, 0.5));
            box-shadow: 0 14px 30px rgba(5, 16, 38, 0.3);
        }

        .ch-page-title {
            margin: 0;
            color: #f2f8ff;
            font-family: 'Sora', sans-serif;
            font-size: clamp(24px, 3vw, 38px);
            line-height: 1.14;
            letter-spacing: -0.02em;
        }

        .ch-page-sub {
            margin: 8px 0 0;
            color: var(--ch-muted);
            font-size: 14px;
            line-height: 1.55;
            max-width: 780px;
        }

        .ch-panel {
            border: 1px solid var(--ch-line);
            border-radius: 16px;
            background: linear-gradient(158deg, var(--ch-card-a), var(--ch-card-b));
            padding: 16px 16px 10px;
            box-shadow: 0 12px 28px rgba(4, 15, 38, 0.24);
            transition: transform 220ms ease, box-shadow 220ms ease, border-color 220ms ease;
        }

        .ch-panel:hover {
            border-color: var(--ch-line-strong);
            box-shadow: 0 16px 34px rgba(8, 24, 58, 0.42);
            transform: perspective(980px) rotateX(2deg) rotateY(-2deg) scale(1.01);
        }

        .ch-mini-note {
            margin: 8px 0 0;
            color: var(--ch-muted);
            font-size: 12px;
        }

        .stTextInput > label,
        .stTextArea > label,
        .stNumberInput > label,
        .stSelectbox > label,
        .stMultiSelect > label,
        .stCheckbox > label {
            color: #dbe9ff !important;
            font-weight: 600 !important;
        }

        div[data-baseweb="input"],
        div[data-baseweb="select"] > div,
        div[data-testid="stTextArea"] textarea,
        div[data-testid="stMultiSelect"] div[data-baseweb="select"] {
            background: rgba(8, 25, 56, 0.74) !important;
            border: 1px solid rgba(126, 181, 252, 0.45) !important;
            border-radius: 11px !important;
        }

        div[data-baseweb="input"] input,
        div[data-testid="stTextArea"] textarea {
            color: #f2f7ff !important;
            -webkit-text-fill-color: #f2f7ff !important;
            background: transparent !important;
        }

        div[data-baseweb="input"] input::placeholder,
        div[data-testid="stTextArea"] textarea::placeholder {
            color: #97b7e1 !important;
        }

        div[data-testid="stFormSubmitButton"] button,
        div.stButton > button {
            border-radius: 11px !important;
            border: 1px solid rgba(168, 210, 255, 0.64) !important;
            background: linear-gradient(145deg, var(--ch-accent), var(--ch-accent-strong)) !important;
            color: #eef7ff !important;
            font-weight: 700 !important;
            transition: transform 180ms ease, filter 180ms ease, box-shadow 180ms ease;
        }

        div[data-testid="stFormSubmitButton"] button:hover,
        div.stButton > button:hover {
            transform: translateY(-1px) scale(1.02);
            filter: brightness(1.08);
            box-shadow: 0 10px 20px rgba(15, 58, 125, 0.45);
        }

        .stMarkdown p,
        .stMarkdown li,
        .stCaption,
        .stInfo,
        .stSuccess,
        .stWarning {
            color: #d9e9ff;
        }

        .stAlert {
            border-radius: 12px;
        }

        @media (max-width: 920px) {
            .ch-page-head {
                padding: 14px 14px 12px;
                margin-bottom: 12px;
            }

            .ch-panel:hover {
                transform: none;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    subtitle_html = f'<p class="ch-page-sub">{escape(subtitle)}</p>' if subtitle else ""
    st.markdown(
        f"""
        <section class="ch-page-head">
            <h1 class="ch-page-title">{escape(title)}</h1>
            {subtitle_html}
        </section>
        """,
        unsafe_allow_html=True,
    )


def panel_start() -> None:
    st.markdown('<div class="ch-panel">', unsafe_allow_html=True)


def panel_end() -> None:
    st.markdown('</div>', unsafe_allow_html=True)
