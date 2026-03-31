"""Optional LangGraph orchestration wrapper.

Core logic remains deterministic services; LangGraph is an additive layer.
"""

from __future__ import annotations

from typing import Any, TypedDict

from app.services.matcher_service import ResumeMatcherService
from app.services.parser_service import ResumeParserService


def _load_langgraph():
    try:
        from langgraph.graph import END, StateGraph

        return END, StateGraph
    except Exception:
        return "END", None


class ResumeAnalysisState(TypedDict, total=False):
    resume_text: str
    jd_text: str
    parsed: dict[str, Any]
    match: dict[str, Any]


def run_resume_analysis_flow(resume_text: str, jd_text: str, parser: ResumeParserService, matcher: ResumeMatcherService) -> dict[str, Any]:
    END, StateGraph = _load_langgraph()

    if StateGraph is None:
        parsed = parser.parse_resume(resume_text)
        match = matcher.match(resume_text, jd_text)
        return {"parsed": parsed, "match": match, "engine": "service-pipeline"}

    def parse_node(state: ResumeAnalysisState) -> ResumeAnalysisState:
        return {"parsed": parser.parse_resume(state["resume_text"]) }

    def match_node(state: ResumeAnalysisState) -> ResumeAnalysisState:
        return {"match": matcher.match(state["resume_text"], state["jd_text"]) }

    graph = StateGraph(ResumeAnalysisState)
    graph.add_node("parse_step", parse_node)
    graph.add_node("match_step", match_node)
    graph.set_entry_point("parse_step")
    graph.add_edge("parse_step", "match_step")
    graph.add_edge("match_step", END)

    app = graph.compile()
    result = app.invoke({"resume_text": resume_text, "jd_text": jd_text})
    result["engine"] = "langgraph"
    return result
