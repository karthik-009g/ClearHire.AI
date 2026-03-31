"""Streamlit app for free resume analysis and optimization (no API key required)."""

from __future__ import annotations

import io

import streamlit as st

from services.docx_service import extract_text_from_docx
from services.pdf_service import extract_text_from_pdf
from services.resume_analyzer_service import analyze_resume
from utils.config import DEFAULT_TARGET_ROLE


st.set_page_config(page_title="Free Resume Analyzer", page_icon="📄", layout="wide")
st.title("Free AI-Style Resume Optimizer")
st.caption("No billing, no API key, and no external AI API calls.")

with st.sidebar:
    st.header("Analysis Controls")
    target_role = st.text_input("Target Role", value=DEFAULT_TARGET_ROLE)
    mode = st.selectbox("Optimization Mode", ["Conservative", "Balanced", "Aggressive"], index=1)
    st.markdown("---")
    st.write("Optional: Paste a Job Description for better keyword matching.")
    jd_text = st.text_area("Job Description", height=200)

uploaded_file = st.file_uploader("Upload Resume (PDF, DOCX, or TXT)", type=["pdf", "docx", "txt"])


def _extract_resume_text() -> str:
    if uploaded_file is None:
        return ""

    suffix = uploaded_file.name.lower().split(".")[-1]

    if suffix == "pdf":
        return extract_text_from_pdf(uploaded_file)

    if suffix == "docx":
        return extract_text_from_docx(uploaded_file)

    if suffix == "txt":
        raw = uploaded_file.read()
        return io.BytesIO(raw).getvalue().decode("utf-8", errors="ignore")

    return ""


if st.button("Analyze Resume", type="primary"):
    if uploaded_file is None:
        st.warning("Please upload a resume file first.")
    else:
        resume_text = _extract_resume_text()

        if not resume_text.strip():
            st.error("Could not extract text. Try another file format or a cleaner resume file.")
        else:
            report = analyze_resume(
                resume_text=resume_text,
                jd_text=jd_text,
                target_role=target_role,
                mode=mode,
            )

            st.subheader("ATS Compatibility Score")
            score = report["ats_score"]
            st.metric("Overall Score", f"{score}/100")
            st.progress(score / 100)

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Contact", report["component_scores"]["contact"])
            c2.metric("Structure", report["component_scores"]["structure"])
            c3.metric("Impact", report["component_scores"]["impact"])
            c4.metric("Keyword Match", report["component_scores"]["keyword_match"])

            tab1, tab2, tab3, tab4 = st.tabs([
                "Strengths & Gaps",
                "Keyword Analysis",
                "Optimized Summary",
                "Bullet Rewrites",
            ])

            with tab1:
                st.markdown("### Strengths")
                for item in report["strengths"] or ["No major strengths detected yet. Add more structured content."]:
                    st.write(f"- {item}")

                st.markdown("### Gaps to Fix")
                for item in report["gaps"] or ["No major gaps found."]:
                    st.write(f"- {item}")

            with tab2:
                st.markdown("### Matched Keywords")
                st.write(", ".join(report["matched_keywords"]) if report["matched_keywords"] else "No match data available")
                st.markdown("### Missing Keywords")
                st.write(", ".join(report["missing_keywords"]) if report["missing_keywords"] else "No major missing keywords")

            with tab3:
                st.markdown("### Suggested Professional Summary")
                st.info(report["optimized_summary"])

            with tab4:
                st.markdown("### Improved Achievement Bullets")
                if report["rewritten_bullets"]:
                    for bullet in report["rewritten_bullets"]:
                        st.write(f"- {bullet}")
                else:
                    st.write("No bullets found. Add bullet points in your experience/projects sections.")

            downloadable_text = [
                f"ATS Score: {report['ats_score']}/100",
                "",
                "Strengths:",
                *[f"- {s}" for s in report["strengths"]],
                "",
                "Gaps:",
                *[f"- {g}" for g in report["gaps"]],
                "",
                "Missing Keywords:",
                ", ".join(report["missing_keywords"]),
                "",
                "Optimized Summary:",
                report["optimized_summary"],
                "",
                "Rewritten Bullets:",
                *[f"- {b}" for b in report["rewritten_bullets"]],
            ]

            st.download_button(
                label="Download Optimization Report",
                data="\n".join(downloadable_text),
                file_name="resume_optimization_report.txt",
                mime="text/plain",
            )

st.markdown("---")
st.caption("Tip: Keep resume sections clearly labeled and add measurable outcomes for higher ATS scores.")
