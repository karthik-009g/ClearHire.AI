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
    parser: Any
    matcher: Any


def _parse_node(state: ResumeAnalysisState) -> ResumeAnalysisState:
    parsed = state.get("parsed")
    if parsed is not None:
        return {"parsed": parsed}
    parser = state.get("parser")
    if parser is not None:
        return {"parsed": parser.parse_resume(state["resume_text"])}
    return {"parsed": {}}


def _match_node(state: ResumeAnalysisState) -> ResumeAnalysisState:
    matcher = state.get("matcher")
    if matcher is not None:
        return {
            "match": matcher.match(
                state["resume_text"],
                state["jd_text"],
                parsed_summary=state.get("parsed"),
            )
        }
    return {"match": {}}


def _compile_graph():
    END, StateGraph = _load_langgraph()
    if StateGraph is None:
        return None
    try:
        graph = StateGraph(ResumeAnalysisState)
        graph.add_node("parse_step", _parse_node)
        graph.add_node("match_step", _match_node)
        graph.set_entry_point("parse_step")
        graph.add_edge("parse_step", "match_step")
        graph.add_edge("match_step", END)
        return graph.compile()
    except Exception:
        return None


# Pre-compile the LangGraph StateGraph once at module scope
_COMPILED_APP = _compile_graph()


def run_resume_analysis_flow(
    resume_text: str,
    jd_text: str,
    parser: ResumeParserService,
    matcher: ResumeMatcherService,
    parsed_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    global _COMPILED_APP
    if _COMPILED_APP is None:
        _COMPILED_APP = _compile_graph()

    if _COMPILED_APP is None:
        parsed = parsed_summary if parsed_summary is not None else parser.parse_resume(resume_text)
        match = matcher.match(resume_text, jd_text, parsed_summary=parsed)
        return {"parsed": parsed, "match": match, "engine": "service-pipeline"}

    initial_state = {
        "resume_text": resume_text,
        "jd_text": jd_text,
        "parser": parser,
        "matcher": matcher,
    }
    if parsed_summary is not None:
        initial_state["parsed"] = parsed_summary

    result = _COMPILED_APP.invoke(initial_state)
    result["engine"] = "langgraph"
    result.pop("parser", None)
    result.pop("matcher", None)
    return result
